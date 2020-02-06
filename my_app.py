import logging
from slackeventsapi import SlackEventAdapter
import detectors
from SlackbotWeb import SlackBotWeb
from flask import Flask
import datetime
import read_files
import queue
import threading
import database_operator
import signal


def get_flask_app(flask_name = __name__):
    """Return flask app"""
    flask_app_name = Flask(flask_name)
    return flask_app_name


def get_slack_event_adapter(SLACK_SIGNING_SECRET, flask_app):
    """Return event adapter of slack"""
    slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, endpoint="/slack/events", server=flask_app)
    return slack_events_adapter


def get_slack_web_adapter(SLACK_BOT_TOKEN, ADMIN_CHANNEL_NAME=''):
    """Return web adapter of slack"""
    slack_web_adapter = SlackBotWeb(SLACK_BOT_TOKEN, ADMIN_CHANNEL_NAME, join_pubic_channels=False)
    return slack_web_adapter


def get_slack_adapters(config_dict, flask_app):
    """Return the web and event slack adapters"""
    slack_events_adapter = get_slack_event_adapter(config_dict['SLACK_SIGNING_SECRET'], flask_app)
    # Using slack admin token instead of slack bot token
    # Admin token allows for deletion of other's messages.
    slack_web_adapter = get_slack_web_adapter(config_dict['SLACK_ADMIN_TOKEN'], config_dict['ADMIN_CHANNEL_NAME'])
    return slack_events_adapter, slack_web_adapter


def skip_process_message(payload):
    """Return true for certain cases"""
    # Skip the case of receiving a message when an admin deletes a message
    event = payload.get("event", {})
    channel_id = event.get("channel")
    # If message is sent in admin channel
    if channel_id == slack_web_adapter.bot_admin_channel_id:
        return True
    # If message is a deleted message
    if (event.get('subtype') is not None) and (event.get('subtype') == 'message_deleted'):
        return True


def get_message_details(payload):
    """Return a list of important message details"""
    # Data structure of payload when the event was message is at https://api.slack.com/events/message
    # Slack is changing the message layout:
    # https://api.slack.com/changelog/2019-09-what-they-see-is-what-you-get-and-more-and-less
    parsed_dict = {}
    event = payload.get("event", {})
    logging.debug("{}--------PAYLOAD-------------{}\n{}".format('*'*20, '*'*20, payload))
    logging.debug("{}--------EVENT-------------{}\n{}".format('#' * 20, '#' * 20, event))

    parsed_dict['team_id'] = payload.get('team_id') if payload.get('team_id') is not None else ''
    parsed_dict['event_id'] = payload.get('event_id') if payload.get('event_id') is not None else ''
    parsed_dict['message_type'] = event.get('type') if event.get('type') is not None else ''
    parsed_dict['message_subtype'] = event.get('subtype') if event.get('subtype') is not None else ''
    parsed_dict['channel_id'] = event.get('channel') if event.get('channel') is not None else ''
    parsed_dict['channel_name'] = slack_web_adapter.get_channel_name(parsed_dict.get('channel_id')) if parsed_dict.get('channel_id') is not None else ''
    parsed_dict['timestamp_epoch'] = event.get('ts') if event.get('ts') is not None else ''
    parsed_dict['timestamp_string'] = datetime.datetime.fromtimestamp(float(parsed_dict.get('timestamp_epoch'))).strftime('%c') if parsed_dict.get('timestamp_epoch') is not None else ''

    # If the field 'blocks' is present
    if event.get('blocks') is not None:
        msg_parse_list = event.get('blocks')[0].get('elements')[0].get('elements')
        msg_text = ''
        for msg_parse_dict in msg_parse_list:
            if msg_parse_dict.get('type') == 'text':
                msg_text += msg_parse_dict.get('text')
            elif msg_parse_dict.get('type') == 'link':
                if msg_parse_dict.get('text') is not None:
                    msg_text += msg_parse_dict.get('text')
                elif msg_parse_dict.get('url') is not None:
                    msg_text += msg_parse_dict.get('url')

        parsed_dict['text'] = msg_text

    elif event.get('subtype') is not None:
        # If Message was changed
        if event.get('subtype') == 'message_changed':
            subtype_msg_structure = event.get('message')
            # If the field 'blocks' is present
            if subtype_msg_structure.get('blocks'):
                subtype_msg_parse_list = subtype_msg_structure.get('blocks')[0].get('elements')[0].get('elements')
                subtype_msg_text=''
                for subtype_msg_parse_dict in subtype_msg_parse_list:
                    if subtype_msg_parse_dict.get('type') == 'text':
                        subtype_msg_text += subtype_msg_parse_dict.get('text')
                    elif subtype_msg_parse_dict.get('type') == 'link':
                        if subtype_msg_parse_dict.get('text') is not None:
                            subtype_msg_text += subtype_msg_parse_dict.get('text')
                        elif subtype_msg_parse_dict.get('url') is not None:
                            subtype_msg_text += subtype_msg_parse_dict.get('url')

                parsed_dict['text'] = subtype_msg_text
            else:
                parsed_dict['text'] = subtype_msg_structure.get('text')

            parsed_dict['user_id'] = subtype_msg_structure.get('user') # Check for which user id to use

    if parsed_dict.get('text') is None:
        if event.get('text') is not None:
            parsed_dict['text'] = event.get('text')
        else:
            parsed_dict['text'] = ''

    if parsed_dict.get('user_id') is None:
        if event.get('user') is not None:
            parsed_dict['user_id'] = event.get('user')
        else:
            parsed_dict['user_id'] = ''

    parsed_dict['user_name'] = slack_web_adapter.get_user_name(parsed_dict.get('user_id')) if len(parsed_dict.get('user_id')) > 0 else ''

    logging.debug("{}--------PARSED_DICT-------------{}\n{}".format('!' * 20, '!' * 20, parsed_dict))
    return parsed_dict


def send_alert_message(alert_msg, user_name, channel_name, time_event_utc, text):
    """Send alert message to admin channel"""
    intro_alert_message = "{}ALERT{}\n".format('#' * 10, '#' * 10)
    intro_alert_message += "User: {}\n".format(user_name)
    intro_alert_message += "Channel: {}\n".format(channel_name)
    intro_alert_message += "Sent time: {} \n".format(time_event_utc)
    intro_alert_message += "Categories: {}\n".format(alert_msg)
    intro_alert_message += "Message Content:\n{}".format(text)
    rem = slack_web_adapter.alert_admin(message_to_send=intro_alert_message, admin_channel=slack_web_adapter.bot_admin_channel_id)
    logging.info('Message sent to Admin:\n{}'.format(intro_alert_message))


def delete_user_message(delete_msg, user_name, channel_id, time_event_epoch):
    """Delete user message"""
    intro_delete_msg = "The previous message sent by {} has been deleted\nReason for deletion: ".format(user_name)
    intro_delete_msg = intro_delete_msg + delete_msg
    response_del = slack_web_adapter.delete_message(channel_id, time_event_epoch)
    response_user_del_msg = slack_web_adapter.send_msg(msg_to_send=intro_delete_msg, channel_to_send=channel_id)


def warn_user_message(warn_msg, user_name, channel_id):
    """Warn user with given message"""
    intro_warn_message = "The previous message sent by {} contains {}\n".format(user_name, warn_msg)
    intro_warn_message += "Please avoid opening the link(s) in this message"
    response_user_warn_msg = slack_web_adapter.send_msg(msg_to_send=intro_warn_message, channel_to_send=channel_id)


def process_message_in_thread():
    """Process the elements in queue """
    while True:

        input_payload = payload_queue.get()
        parsed_dict = get_message_details(input_payload)
        # If the message has to be skipped for analysis
        if skip_process_message(input_payload):
            # Get the default dictionary for all policy items
            result_dict = detectors.call_detectors('', policy_dict, suspicious_dict)
            # Insert the event into database
            database_operator.insert_into_table(database_con, database_cursor, parsed_dict, result_dict, database_ordered_dict)
            payload_queue.task_done()
            # Move to the next element of the queue
            continue

        result_dict = detectors.call_detectors(parsed_dict['text'], policy_dict, suspicious_dict)

        # Insert the event into database
        database_operator.insert_into_table(database_con, database_cursor, parsed_dict, result_dict, database_ordered_dict)
        logging.debug(result_dict)
        alert_msg = ''
        delete_msg = ''
        warn_msg = ''

        for key, value in result_dict.items():
            if value.get('is_True') is True:
                alert_msg = alert_msg + key + ' '
            if value.get('to_Delete') is True:
                delete_msg = delete_msg + key + ' '
            if value.get('to_Warn') is True:
                warn_msg = warn_msg + key + ' '

        # If the messaged contained anything to flag
        if len(alert_msg) > 0:
            # If the message has to be deleted
            if len(delete_msg) > 0:
                delete_user_message(delete_msg, parsed_dict['user_name'], parsed_dict['channel_id'],
                                    parsed_dict['timestamp_epoch'])
            # Else if the user has to be warned
            elif len(warn_msg) > 0:
                warn_user_message(warn_msg, parsed_dict['user_name'], parsed_dict['channel_id'])

            send_alert_message(alert_msg, parsed_dict['user_name'], parsed_dict['channel_name'],
                               parsed_dict['timestamp_string'], parsed_dict['text'])

        payload_queue.task_done()


def process_message(payload):
    """Process the received message"""
    payload_queue.put(payload)


def clean_up_signal_handler(sig_num, stack_frame):
    """Perform cleanup operations"""
    try:
        database_operator.close_database_connector_cursor(database_con, database_cursor)
    except NameError as e:
        logging.info("Database connector and cursor have not been initialized")
    finally:
        logging.info("Exit signal received")
        logging.info("Exiting gracefully")
        exit(0)


# Read the JSON config file which contains slack bot token, slack admin token, slack signing secret, admin channel name
config_dict = read_files.read_json_data('config_details.json')
policy_dict, suspicious_dict = read_files.get_suspicious_items_dict('policy_details.json')

# Initialize logging
logging.basicConfig(filename=config_dict.get('LOG_FILE_PATH'), format='%(levelname)s:%(asctime)s:%(name)s:%(message)s', level=logging.DEBUG)

# Get the flask application
flask_app = get_flask_app()

slack_events_adapter, slack_web_adapter = get_slack_adapters(config_dict, flask_app)
process_message = slack_events_adapter.on(event='message', f=process_message)

# Read the database config file
database_ordered_dict = read_files.read_json_data('database_details.json', order=True)
database_con, database_cursor = database_operator.get_database_connector_cursor(database_ordered_dict, initialize_table=True)

# Initialize a queue, and start a daemon thread to process elements in queue
payload_queue = queue.Queue()
thread_worker = threading.Thread(target=process_message_in_thread, daemon=True)
thread_worker.start()

# Handle signals
try:
    signal.signal(signal.SIGINT, clean_up_signal_handler)
except AttributeError as e:
    logging.error(e)
try:
    signal.signal(signal.SIGTERM, clean_up_signal_handler)
except AttributeError as e:
    logging.error(e)


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=8000)



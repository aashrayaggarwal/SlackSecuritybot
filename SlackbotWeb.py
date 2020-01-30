import os
import slack

class SlackBotWeb():
    def __init__(self, slack_bot_token, admin_private_channel_name = '', join_pubic_channels=False, public_channels_names=[]):
        """ Instantiate the slackbot """
        try:
            self.slack_client = slack.WebClient(token=slack_bot_token)
            response = self.slack_client.auth_test()
        except slack.errors.SlackApiError as e:
            print("Invalid Authentication token for bot")
        else:
            print('helll')
            print(response)
            response_data = response.data
            print(response_data)
            self.bot_team_name = response_data.get('team')
            self.bot_user_name = response_data.get('user')
            self.bot_team_id = response_data.get('team_id')
            self.bot_user_id = response_data.get('user_id')
            if response_data.get('bot_id'):
                self.bot_bot_id = response_data.get('bot_id')
                self.is_bot_user = True
            else:
                self.is_bot_user = False

            if join_pubic_channels:
                self.join_public_channels(public_channels_names)

            if len(admin_private_channel_name) > 0:
                self.bot_admin_channel_id = self.get_admin_channel_id(admin_private_channel_name)

    def send_msg(self, msg_to_send='Hi, I am a bot', channel_to_send='#random'):
        try:
            response = self.slack_client.chat_postMessage(channel=channel_to_send, text=msg_to_send)
        except slack.errors.SlackApiError as e:
            print (e)
            return False
        else:
            return True

    def join_public_channels(self, public_channels_names_to_join=[]):
        """Join specified public channels that the bot is not currently a member of
        The bot will join all public channels if no argument/empty tuple is given
        """
        if len(public_channels_names_to_join) == 0:
            join_all_public_channels = True
        else:
            join_all_public_channels = False

        response = self.slack_client.conversations_list(types='public_channel')
        public_channels_list = response.data.get('channels')
        for public_channel_dict in public_channels_list:
            channel_id = public_channel_dict.get('id')
            channel_name = public_channel_dict.get('name')
            if join_all_public_channels or (channel_name in public_channels_names_to_join):
                if not (public_channel_dict.get('is_member')):
                    self.slack_client.conversations_join(channel=channel_id)
                    print("Bot user joined {} channel".format(channel_name))
                else:
                    print("Bot user is already a member of {} channel".format(channel_name))

                # Remove these channels from public_channels_names_to_join list
                public_channels_names_to_join = [i for i in public_channels_names_to_join if i != channel_name]

        for channel_not_visible in public_channels_names_to_join:
            print("Bot cannot see channel {}".format(channel_not_visible))

        return True

    def leave_public_channels(self, public_channels_names_to_remove=[]):
        """Leave specified public channels or all public channels if nothing is specified"""
        if len(public_channels_names_to_remove) == 0:
            leave_all_public_channels = True
        else:
            leave_all_public_channels = False

        response = self.slack_client.conversations_list(types='public_channel')
        public_channels_list = response.data.get('channels')
        for public_channel_dict in public_channels_list:
            channel_id = public_channel_dict.get('id')
            channel_name = public_channel_dict.get('name')
            if leave_all_public_channels or (channel_name in public_channels_names_to_remove):
                if public_channel_dict.get('is_member'):
                    self.slack_client.conversations_leave(channel=channel_id)
                    print ("Bot user left {} channel".format(channel_name))
                else:
                    print("Bot user is not member of {} channel. Skipping this channel".format(channel_name))

            # Remove these channels from public_channels_names_to_join list
            public_channels_names_to_remove = [i for i in public_channels_names_to_remove if i != channel_name]
        for channel_not_visible in public_channels_names_to_remove:
            print("Bot cannot see channel {}".format(channel_not_visible))

        return True

    def alert_admin(self,  message_to_send, admin_channel):
        # A channel should be there with bot as its member
        return self.send_msg(message_to_send, admin_channel)

    def get_admin_channel_id(self, admin_private_channel_name):
        """Return the ID of admin private channel"""
        response = self.slack_client.conversations_list(types='private_channel')
        private_channels_list = response.data.get('channels')
        for private_channel_dict in private_channels_list:
            if private_channel_dict.get('name') == admin_private_channel_name:
                return private_channel_dict.get('id')
        print ("Private channel {} does not exist".format(admin_private_channel_name))
        return None

    def get_user_details(self, user_id):
        """Return a dictionary containing user details of user associated with given user_id"""
        if user_id is None:
            print("User ID is none")
            return
        try:
            response = self.slack_client.users_info(user=user_id)
        except slack.errors.SlackApiError as e:
            print (e)
            return False
        else:
            return response.data.get('user')

    def get_channel_details(self, channel_id):
        """Return a dictionary containing channel details of user associated with given channel_id"""
        try:
            response = self.slack_client.conversations_info(channel=channel_id)
        except slack.errors.SlackApiError as e:
            print (e)
            return False
        else:
            return response.data.get('channel')

    def get_user_name(self, user_id):
        """Return the username of a user given his user id """
        if user_id is None:
            print("User ID is none")
            return
        user_details = self.get_user_details(user_id)
        return user_details.get('real_name')

    def get_channel_name(self, channel_id):
        """Return the channel name of a channel given its channel id """
        channel_details = self.get_channel_details(channel_id)
        return channel_details.get('name')

    def delete_message(self, channel_id, timestamp_message):
        """Delete message sent at a particular time from the specified channel"""
        try:
            response = self.slack_client.chat_delete(channel=channel_id, ts=timestamp_message)
        except slack.errors.SlackApiError as e:
            print (e)
            return False
        else:
            return True

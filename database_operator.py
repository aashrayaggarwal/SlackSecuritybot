import psycopg2
import datetime
import logging


def connect_to_database(database_ordered_dict):
    """Return the connector and cursor to database"""
    try:
        database_con = psycopg2.connect(host=database_ordered_dict.get('host'), port=database_ordered_dict.get('port'), database=database_ordered_dict.get('database'))
        database_cursor = database_con.cursor()
    except Exception as e:
        logging.error(e)
        return False
    else:
        logging.info("Initialized database connector and cursor")
        return database_con, database_cursor


def close_database_connector_cursor(database_con, database_cursor):
    """Close database connector and cursor"""
    try:
        database_cursor.close()
        database_con.close()
    except Exception as e:
        logging.error(e)
        return False
    else:
        logging.info("Closed database connector and cursor")
        return True


def create_initial_table(database_con, database_cursor, table_name, table_fields):
    """Create initial table if it does not exist"""
    sql_query = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)

    for column_name, column_type in table_fields.items():
        sql_query = sql_query + column_name + " " + column_type + ","

    if sql_query[-1] == ',':
        sql_query = sql_query[:-1] + ')'

    try:
        res = database_cursor.execute(sql_query)
        database_con.commit()
    except Exception as e:
        logging.error(e)
        return False
    else:
        return True


def get_database_connector_cursor(database_ordered_dict, initialize_table=True):
    """Get a database connector and cursor.
    If initialize_table is set to True, the table with 'table_name' key in the given dictionary is created if the that table did not exist already"""
    database_con, database_cursor = connect_to_database(database_ordered_dict)
    if initialize_table is True:
        create_initial_table(database_con, database_cursor, database_ordered_dict.get('table_name'), database_ordered_dict.get('table_fields'))

    return database_con, database_cursor


def create_insertion_dict(message_dict, flags_dict):
    """Return a dictionary whose keys and values would be inserted in the SQL database"""
    database_insert_dict = {
        'message_type': message_dict.get('message_type'),
        'message_subtype': message_dict.get('message_subtype'),
        'channel_id': message_dict.get('channel_id'),
        'channel_name': message_dict.get('channel_name'),
        'team_id': message_dict.get('team_id'),
        'user_id': message_dict.get('user_id'),
        'user_name': message_dict.get('user_name'),
        'event_id': message_dict.get('event_id'),
        'timestamp_epoch': datetime.datetime.utcfromtimestamp(float(message_dict.get('timestamp_epoch'))).isoformat(),
        'text': message_dict.get('text'),
        'atleast_one_http_link': flags_dict.get('atleast_one_http_link').get('is_True'),
        'invalid_ssl_cert': flags_dict.get('invalid_ssl_cert').get('is_True'),
        'malicious_link': flags_dict.get('malicious_links').get('is_True'),
        'phishing_link': flags_dict.get('phishing_links').get('is_True'),
        'offensive_word': flags_dict.get('offensive_words').get('is_True')
    }
    return database_insert_dict


def insert_from_dict_into_table(database_con, database_cursor, database_insert_dict, table_to_insert):
    """Insert data from the dictionary into given table"""
    sql_query = "INSERT INTO {} (".format(table_to_insert)
    values_string = ' VALUES('
    values_list = []

    for column_name, value in database_insert_dict.items():
        sql_query = sql_query + column_name + ","
        values_string = values_string + '%s,'
        values_list.append(value)

    if values_string[-1] == ',':
        values_string = values_string[:-1] + ')'

    if sql_query[-1] == ',':
        sql_query = sql_query[:-1] + ')'

    sql_query = sql_query + values_string

    try:
        res = database_cursor.execute(sql_query, (*values_list,))
        database_con.commit()
    except Exception as e:
        logging.error(e)
        return False
    else:
        logging.info("Inserted data in {} table".format(table_to_insert))
        return True


def insert_into_table(database_con, database_cursor, message_dict, flags_dict, database_ordered_dict):
    """Insert data from the two given dictionaries into a table"""
    database_insert_dict = create_insertion_dict(message_dict, flags_dict)
    table_to_insert = database_ordered_dict.get('table_name')
    return insert_from_dict_into_table(database_con, database_cursor, database_insert_dict, table_to_insert)
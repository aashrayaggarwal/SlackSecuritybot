import json


def read_json_data(input_file):
    """Return the json dict containing config details"""
    with open(input_file, 'r') as file_handle:
        json_dict = json.load(file_handle)
    return json_dict


def read_suspicious_items(policy_dict):
    """Return a dictionary containing suspicious items"""
    suspicious_dict = {}

    for filter_name, filter_details in policy_dict.items():
        filter_database_path = filter_details.get('database_path')
        if len(filter_database_path) == 0:
            suspicious_dict[filter_name] = []
            continue
        with open(filter_database_path, 'r') as file_handle:
            flag_items = file_handle.read().splitlines()
            suspicious_dict[filter_name] = flag_items

    return suspicious_dict


def get_suspicious_items_dict(input_file):
    """Return a dictionary of policy details, and suspicious items"""
    policy_dict = read_json_data(input_file)
    suspicious_dict = read_suspicious_items(policy_dict)
    return policy_dict, suspicious_dict
import detector_modules


def call_detectors(message, policy_dict, suspicious_dict):
    """Pass the input message through all filters"""

    detector_dict = {}
    for policy_name, policy_values in policy_dict.items():
        detector_dict[policy_name] = {'is_True':False, 'to_Delete':False, 'to_Warn':False}

        # If length of message is zero, create a default dictionary for all policy items
        if (len(message) == 0) or message is None:
            continue

        # Get the detector function that should be called
        imported_detector_func = getattr(detector_modules, policy_values.get('detector_func'))

        # If the policy does not have a list, call the detector function without that list
        if len(suspicious_dict.get(policy_name)) == 0:
            detector_dict[policy_name]['is_True'] = imported_detector_func(message)
        elif len(suspicious_dict.get(policy_name)) > 0:
            detector_dict[policy_name]['is_True'] = imported_detector_func(message, suspicious_dict.get(policy_name))

        # If the policy file says to delete the message AND the message is flagged by the detector function
        # Set the value of 'to_Delete' in 'detector_dict' to True
        if policy_values.get('to_Delete') is True and detector_dict.get(policy_name).get('is_True') is True:
            detector_dict.get(policy_name)['to_Delete'] = True

        # If the policy file says to warn about the message AND the message is flagged by the detector function
        # Set the value of 'to_Delete' in 'detector_dict' to True
        if policy_values.get('to_Warn') is True and detector_dict.get(policy_name).get('is_True') is True:
            detector_dict.get(policy_name)['to_Warn'] = True

    return detector_dict

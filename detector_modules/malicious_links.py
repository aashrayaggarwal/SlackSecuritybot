def detect_malicious_links(message, malicious_links_list):
    """Check if the message contains a known malicious link"""
    for malicious_link in malicious_links_list:
        if malicious_link.casefold() in message.casefold():
            return True

    return False
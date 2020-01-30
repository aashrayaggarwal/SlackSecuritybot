def detect_phishing_links(message, phishing_links_list):
    """Check if the message contains a known phishing link"""
    for phishing_link in phishing_links_list:
        if phishing_link.casefold() in message.casefold():
            return True

    return False
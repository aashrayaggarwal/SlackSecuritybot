def detect_offensive_words(message, offensive_list):
    """Check if the message contains a word from offensive list"""
    words_in_message = message.lower().split()
    for word in words_in_message:
        if word in offensive_list:
            return True
    return False
import re
import requests


def detect_atleast_one_invalid_ssl_link(message):
    """Return true if the message contains atleast one link with invalid SSL cert"""
    # Regex for finding URL
    reg_pattern = re.compile(r'(?:(?:https?):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+')
    reg_url = reg_pattern.findall(message)
    for url_match in reg_url:
        contains_prefix = True
        if ('http://' not in url_match) and ('https://' not in url_match):
            # In case a website uses HTTPS, the requests library will follow redirect from HTTP page to HTTPS page
            url_match = 'http://' + url_match
        try:
            req_con = requests.get(url_match)
        except requests.exceptions.SSLError as e:
            return True
        except requests.exceptions.InvalidURL as e:
            continue
        except requests.exceptions.ConnectionError as e:
            continue

    return False
import re
import requests


def detect_atleast_one_http_link(message):
    """Return true if the message contains atleast one HTTP link"""
    # Regex for finding URL
    reg_pattern = re.compile(r'(?:(?:http):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+')
    reg_url = reg_pattern.findall(message)
    for url_match in reg_url:
        if ('http://' not in url_match) and ('https://' not in url_match) :
            url_match = 'http://' + url_match
        try:
            req_con = requests.get(url_match)
        except requests.exceptions.SSLError as e:
            continue
        except requests.exceptions.ConnectionError as e:
            continue
        except requests.exceptions.InvalidURL as e:
            continue
        else:
            if ('https://' not in req_con.url) and ('http://' in req_con.url):
                return True

    return False

import contextlib
import re
import urllib.parse

import requests


def format_url(url: str) -> str:
    url = url.strip()
    url = urllib.parse.quote(url)
    if not re.match('^(http|https)://', url):
        url = f"https://{url}"
    return url


def simple_get(url):
    url = format_url(url)
    try:
        with contextlib.closing(requests.get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return
    except requests.RequestException as e:
        print(f"Error during requests to {url} : {str(e)}")
        return


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

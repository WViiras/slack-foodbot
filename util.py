import contextlib
import os
import re
import typing
import urllib.parse

import requests
import slackclient
import yaml

resources_path = os.path.join("resources")
site_resources_path = os.path.join(resources_path, "sites")
templates_path = os.path.join(resources_path, "templates")
conf_file_path = os.path.join(resources_path, "conf.yaml")

with open(conf_file_path, "r") as f:
    configuration = yaml.load(f)

template_daily_msg = "msg-daily"
template_daily_header = "msg-header"
template_msg_food_item = "msg-daily-food"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SlackUtil(metaclass=Singleton):

    def __init__(self):
        slack_token = self._get_slack_token()
        if not slack_token.strip():
            raise Exception("no token given!")
        self._slack_client = slackclient.SlackClient(slack_token)

    @staticmethod
    def _get_slack_token() -> str:
        return configuration["slack"]["token"]

    def send_to_slack(self, method=None, channel=None, **kwargs):
        print(f"method='{method}'; channel='{channel}'; kwargs='{kwargs}'")

        if not method:
            raise Exception("No method provided")

        response = None
        response = self._slack_client.api_call(
            method,
            channel=channel,
            **kwargs)
        print(response)


def join_path(path, *paths):
    return os.path.join(path, *paths)


def read_site_file_lines(site: str, filename: str) -> typing.List[str]:
    site_file_path = join_path(site_resources_path, site, filename)
    with open(site_file_path, encoding="utf-8") as f:
        return f.readlines()


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


def get_msg_template(template: str):
    template_path = join_path(templates_path, template)
    with open(template_path) as f:
        return f.read()

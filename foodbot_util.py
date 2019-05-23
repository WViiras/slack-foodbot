import typing

import yaml

from util import common_util

resources_path = common_util.join_path("slack_foodbot", "resources")
site_resources_path = common_util.join_path(resources_path, "sites")
templates_path = common_util.join_path(resources_path, "templates")
conf_file_path = common_util.join_path(resources_path, "slack_conf.yaml")

with open(conf_file_path, "r") as f:
    configuration = yaml.load(f)

template_daily_msg = "msg-daily"
template_daily_header = "msg-header"
template_msg_food_item = "msg-daily-food"


def read_site_file_lines(site: str, filename: str) -> typing.List[str]:
    site_file_path = common_util.join_path(site_resources_path, site, filename)
    with open(site_file_path, encoding="utf-8") as f:
        return f.read().splitlines()


def get_msg_template(template: str):
    template_path = common_util.join_path(templates_path, template)
    with open(template_path) as f:
        return f.read()


def get_slack_token() -> str:
    return configuration["slack"]["token"]

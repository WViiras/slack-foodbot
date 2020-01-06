import typing
from pathlib import Path

import yaml

resources_path = Path("resources")
site_resources_path = Path(resources_path, "sites")
template_resources_path = Path(resources_path, "templates")
conf_file_path = Path(resources_path, "configuration.yaml")

with open(conf_file_path, "r") as cnf_f:
    configuration = yaml.load(cnf_f)

template_daily_msg = "msg-daily"
template_daily_header = "msg-header"
template_msg_food_item = "msg-daily-food"


def read_site_file_lines(site: str, filename: str) -> typing.List[str]:
    site_file_path = Path(site_resources_path, site, filename)
    with open(site_file_path, encoding="utf-8") as f:
        return f.read().splitlines()


def get_msg_template(template: str):
    template_path = Path(template_resources_path, template)
    with open(template_path) as f:
        return f.read()


def get_slack_token() -> str:
    return configuration["slack"]["token"]

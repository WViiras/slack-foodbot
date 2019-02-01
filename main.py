import abc
import datetime
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

import util


class Site:
    def __init__(self, site_name: str):
        if site_name is None:
            raise Exception("No site name provided")
        self.site_name = site_name

        site_urls = util.read_site_file_lines(site_name, "url")
        self.pretty_url = site_urls[1].strip()
        self.download_url = site_urls[0].strip()

        self.locale_name: str = None
        self.daily_offers: List[Tuple[str, str]] = None

        self.generate_menu()

    def get_soup(self) -> BeautifulSoup:
        site = util.simple_get(self.download_url)
        return BeautifulSoup(site, features="html.parser")

    @abc.abstractmethod
    def generate_menu(self) -> Dict:
        pass

    def generate_menu_string(self) -> str:
        print(f"generate_menu_string for {self.locale_name}")

        food_item_template = util.get_msg_template(util.template_msg_food_item)

        offers_part = ""

        for item, cost in self.daily_offers:
            item_name = str(item)
            item_cost = str(cost)
            offers_part += food_item_template \
                .replace("::FOOD:", item_name.strip()) \
                .replace("::PRICE:", item_cost)

        daily_menu = util.get_msg_template(util.template_daily_msg)
        daily_menu = daily_menu \
            .replace("::NAME:", self.locale_name) \
            .replace("::OFFERS:", offers_part) \
            .replace("::URL:", self.pretty_url) \
            .replace("::EXTRA:", "")

        # print(daily_menu)

        return daily_menu


class Reval(Site):
    REVAL_DAY_MATCH = {
        "Esmaspäeval": "Monday",
        "Teisipäeval": "Tuesday",
        "Kolmapäeval": "Wednesday",
        "Neljapäeval": "Thursday",
        "Reedel": "Friday",
        "Laupäeval": "Saturday",
        "Pühapäeval": "Sunday"
    }

    def generate_menu(self) -> Dict:
        print(f"find_daily {self.site_name}")
        soup: BeautifulSoup = self.get_soup()
        if soup is None:
            return Paevapakkumised("reval-tere").generate_menu()
            # return paevapakkumised.find_daily_from_paevapakkumised(site_name)

        menu_div: Tag = soup.find(name="div", attrs={"block02_e content"})
        menu_lines: Tag = menu_div.findAll(name="p")
        menu_line: Tag
        for menu_line in menu_lines:
            tere_kohvik = "TERE KOHVIKUS"
            if tere_kohvik in menu_line.text:
                print("")
                pass
            print(menu_line.text)
            pass

        pass

    def __day_to_reval_day(self, date: datetime.datetime) -> str:
        day_name = date.strftime("%A")
        return self.REVAL_DAY_MATCH.get(day_name)


class Paevapakkumised(Site):

    def generate_menu(self):
        print(f"generate_menu for {self.site_name}")
        soup = self.get_soup()
        if soup is None:
            return None

        meal_selected_div: Tag = soup.find(name="div", attrs={"meal selected"})
        offers: ResultSet = meal_selected_div.findAll(name="div", attrs="offer")

        daily_offers: List[Tuple[str, str]] = []
        for offer in offers:
            contents = offer.contents
            food = contents[0]
            cost = contents[1].text
            daily_offers.append((food, cost))

        self.locale_name: str = meal_selected_div.find(name="div", attrs="header").text.strip()
        self.daily_offers = daily_offers


def generate_daily_msg_string(sites: List[Site]) -> str:
    menu_strings = []
    for site in sites:
        site_menu = site.generate_menu_string()
        menu_strings.append(site_menu)

    menu_string = "\n".join(menu_strings)

    msg = util.get_msg_template(util.template_daily_header)

    today = datetime.datetime.now().strftime("%d-%m-%Y")
    msg = msg \
        .replace("::DATE:", today) \
        .replace("::MENU:", menu_string) \
        .strip()

    return msg


def generate_daily_menu():
    menu_generators = dict()
    menu_generators["reval-tere"] = Paevapakkumised
    # menu_generators["reval"] = Reval
    menu_generators["akbana"] = Paevapakkumised

    sites: List[Site] = []
    for site_name, menu_generator in menu_generators.items():
        try:
            site_menu_generator: Site = menu_generator(site_name)
            sites.append(site_menu_generator)
        except Exception as e:
            print(e)

    return generate_daily_msg_string(sites)


def get_custom_text():
    filename = "custom.msg"
    file_path = util.join_path(util.resources_path, filename)
    with open(file_path, 'r') as f:
        return f.read().strip()


def main(**kwargs):
    util.SlackUtil(token=kwargs.get("token"))  # init SlackUtil

    channel = kwargs.get("channel")

    method = "chat.postMessage",
    slack_kwargs = {}

    if kwargs.get("custom"):
        text = get_custom_text()
    else:
        text = generate_daily_menu()

    slack_kwargs["text"] = text

    util.SlackUtil().send_to_slack(method, channel, **slack_kwargs)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-token")
    parser.add_argument("-custom", action="store_true")
    parser.add_argument("-channel")

    args = vars(parser.parse_args())
    print(f"running with arguments: '{args}'")
    main(**args)
    print("==foodbot done==")

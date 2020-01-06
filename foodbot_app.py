import abc
import re
from datetime import datetime
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from slack_foodbot import foodbot_util
from util import common_util, slack_util

# import pytesseract
# import cv2

from pathlib import Path


class Site:
    def __init__(self, site_name: str):
        if site_name is None:
            raise Exception("No site name provided")
        self.site_name = site_name

        site_urls = foodbot_util.read_site_file_lines(site_name, "url")
        self.pretty_url = site_urls[1].strip()
        self.download_url = site_urls[0].strip()

        self.locale_name: str = None

        self.daily_offers = self.generate_menu()

    def get_soup(self) -> BeautifulSoup:
        site = common_util.simple_get(self.download_url)
        return BeautifulSoup(site, features="html.parser")

    @abc.abstractmethod
    def generate_menu(self) -> Dict:
        pass

    def generate_menu_string(self) -> str:
        print(f"generate_menu_string for {self.locale_name}")

        food_item_template = foodbot_util.get_msg_template(foodbot_util.template_msg_food_item)

        offers_part = ""

        for item, cost in self.daily_offers:
            item_name = str(item)
            item_cost = str(cost)
            offers_part += food_item_template \
                .replace("::FOOD:", item_name.strip()) \
                .replace("::PRICE:", item_cost)

        daily_menu = foodbot_util.get_msg_template(foodbot_util.template_daily_msg)
        daily_menu = daily_menu \
            .replace("::NAME:", self.locale_name) \
            .replace("::OFFERS:", offers_part) \
            .replace("::URL:", self.pretty_url)

        # print(daily_menu)

        return daily_menu


class Tondi:
    def __init__(self, site_name):
        self.daily_offers = self.generate_menu()

    def generate_menu_string(self):
        print(f"generate_menu_string for Tondi")

        daily_menu = [line for line in self.daily_offers.split("\n") if line != ""]
        about_open_cv = "\n\nTondi Grill was brought to you by Open CV and Google Tesseract OCR " \
                        "\nhttps://opencv.org/about/" \
                        "\nhttps://opensource.google.com/projects/tesseract"
        daily_menu = "\n".join(daily_menu) + about_open_cv

        return daily_menu

    def generate_menu(self) -> Dict:
        img = cv2.imread("slack_foodbot/resources/tondi_1.jpg")
        img_scaled = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        text = pytesseract.image_to_string(img_scaled)
        return text


class Reval(Site):
    REVAL_DAY_ENG_EST = {
        "Monday": "Esmaspäeval",
        "Tuesday": "Teisipäeval",
        "Wednesday": "Kolmapäeval",
        "Thursday": "Neljapäeval",
        "Friday": "Reedel",
        "Saturday": "Laupäeval",
        "Sunday": "Pühapäeval"
    }
    REVAL_DAY_EST_ENG = {
        "Esmaspäeval": "Monday",
        "Teisipäeval": "Tuesday",
        "Kolmapäeval": "Wednesday",
        "Neljapäeval": "Thursday",
        "Reedel": "Friday",
        "Laupäeval": "Saturday",
        "Pühapäeval": "Sunday"
    }

    @staticmethod
    def _check_post_date(soup: BeautifulSoup) -> bool:
        date_div: Tag = soup.find(name="div", attrs={"class": "title-wrap"}) \
            .find(name="h1")
        for content in date_div.contents:
            content = content.strip()
            if "Lõunamenüü pakkumised" in content:
                date_format = "%d.%m.%y"
                date_format_regex = r"(\d{2}\.\d{2})|(\d{2}$)"
                dates = re.findall(date_format_regex, content)
                start_date = dates[0][0]
                end_date = dates[1][0]
                year = dates[2][1]
                start_date = datetime.strptime(f"{start_date}.{year}", date_format)
                end_date = datetime.strptime(f"{end_date}.{year}", date_format)
                return start_date <= datetime.now() <= end_date

    def _generate_from_reval(self) -> List[Tuple]:
        print(f"find_daily {self.site_name}")
        # reval_html = util.mock_download_reval()
        # soup: BeautifulSoup = BeautifulSoup(reval_html, features="html.parser")
        soup: BeautifulSoup = self.get_soup()
        if soup is None:
            return

        # check date
        is_valid_date = self._check_post_date(soup)
        if not is_valid_date:
            return

        # fund menu
        menu_div: Tag = soup.find(name="div", attrs={"class": "block02_e content"})
        menu_lines = menu_div.findAll(name="p")

        menu_lines = _flatten_list([line.text for line in menu_lines])

        offers = self._find_city_offers("TALLINN", menu_lines)

        daily_offers = []
        compiled = re.compile(r"(\d\..+$)")
        for i, offer in enumerate(offers):
            cost = compiled.findall(offer)[-1]
            const_index: int = offer.index(cost)
            offer = offer[:const_index].strip()
            daily_offers.append((offer, cost))
        return daily_offers

    def _find_city_offers(self, city, menu_lines):
        offers = []
        day = self._get_today_as_reval_day()
        is_past_tallinn = False
        for i, line in enumerate(menu_lines):
            if city in line:
                is_past_tallinn = True
            if is_past_tallinn:
                if day in line:
                    offers.append(menu_lines[i + 1])
                    offers.append(menu_lines[i + 2])
                    return offers

    def generate_menu(self) -> Dict:
        self.locale_name = "Reval Café"
        menu = self._generate_from_reval()
        if not menu:
            menu = Paevapakkumised("reval-tere").generate_menu()
        return menu

    def _get_today_as_reval_day(self) -> str:
        today = datetime.now().strftime("%A")
        return self.REVAL_DAY_ENG_EST.get(today)
        # return "Kolmapäeval"


class Paevapakkumised(Site):

    def generate_menu(self):
        print(f"generate_menu for {self.site_name}")
        soup = self.get_soup()
        if soup is None:
            return

        meal_selected_div: Tag = soup.find(name="div", attrs={"meal selected"})
        offers: ResultSet = meal_selected_div.findAll(name="div", attrs="offer")

        daily_offers: List[Tuple[str, str]] = []
        for offer in offers:
            contents = offer.contents
            food = contents[0]
            if "Hetkel kahjuks pakkumised puuduvad" in food:
                return None
            cost = contents[1].text
            daily_offers.append((food, cost))

        self.locale_name: str = meal_selected_div.find(name="div", attrs="header").text.strip()
        return daily_offers


def _flatten_list(full_list: List[str]):
    full_list = [_.strip().splitlines() for _ in full_list]
    flat_list = [line for sublist in full_list for line in sublist]
    flat_list = [item for item in flat_list if item.strip()]
    return flat_list


def generate_daily_msg_string(sites: List[Site]) -> str:
    menu_strings = []
    for site in sites:
        site_menu = site.generate_menu_string()
        menu_strings.append(site_menu)

    menu_string = "\n".join(menu_strings)

    msg = foodbot_util.get_msg_template(foodbot_util.template_daily_header)

    today = datetime.now().strftime("%d-%m-%Y")
    msg = msg \
        .replace("::DATE:", today) \
        .replace("::MENU:", menu_string) \
        .strip()

    return msg


def generate_daily_menu():
    menu_generators = dict()
    menu_generators["reval-tere"] = Paevapakkumised
    # menu_generators["daily"] = Paevapakkumised
    menu_generators["tondi"] = Tondi
    # menu_generators["reval"] = Reval
    # menu_generators["akbana"] = Paevapakkumised

    sites: List[Site] = []
    for site_name, menu_generator in menu_generators.items():
        try:
            site_menu_generator = menu_generator(site_name)
            if site_menu_generator.daily_offers:
                sites.append(site_menu_generator)
        except Exception as e:
            print(e)

    if not sites:
        return

    menu_string = generate_daily_msg_string(sites)

    print("generated daily menu")
    print(menu_string)
    return menu_string


def get_custom_text(filename):
    file_path = common_util.join_path(foodbot_util.resources_path, filename)
    with open(file_path, 'r') as f:
        return f.read().strip()
    # text = ">>>"
    # img = cv2.imread(filename)
    # text += pytesseract.image_to_string(img)
    # text = "This was brought to you by Open CV \nhttps://opencv.org/about/"
    # return {"text": text}


def main(**kwargs):
    # slack_util.SlackClient(foodbot_util.get_slack_token())  # init SlackUtil

    channel = kwargs.get("channel")

    response = None
    custom_path = kwargs.get("custom_path")
    image_path = kwargs.get("image_path")
    if custom_path is not None:
        message_content = get_custom_text(custom_path)
        response = slack_util.BotClient().client.chat_postMessage(channel=channel, text=message_content)
    elif image_path is not None:
        print(f"File from path {image_path}")
        response = slack_util.BotClient().client.files_upload(file=image_path, channels=channel)
    else:
        message_content = generate_daily_menu()
        if not message_content:
            return
        response = slack_util.BotClient().client.chat_postMessage(channel=channel, text=message_content)

    print(f"response: \n{response}\n")

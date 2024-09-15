import gettext
import logging
from pathlib import Path
import re

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import pycountry as pc
import pycountry_convert as pcc
import requests

from src.utils import setup_logging, CATEGORIES, TAGS, INVEST_TYPES, CONTINENT_MAPPING

setup_logging()
logger = logging.getLogger(__name__)

german = gettext.translation('iso3166-1', pc.LOCALES_DIR, languages=['de'])
german.install()


def str_to_float(string: str):
    string = string.replace('\xa0%', '')
    string = string.replace(',', '.')

    return float(string)


def get_official_country_name(query_name: str):
    """Compare query_name with all official country names to find match"""
    for c in pc.countries:
        german_name = german.gettext(c.name)

        similarity_score = fuzz.partial_ratio(query_name.lower(), german_name.lower())
        if similarity_score > 85:
            return german_name

    return query_name


def get_continent(country_id: str):
    """Get continent from country ID"""
    try:
        continent_code = pcc.country_alpha2_to_continent_code(country_id)
        continent_name = pcc.convert_continent_code_to_continent_name(continent_code)
        return CONTINENT_MAPPING.get(continent_name, continent_name)
    except KeyError:
        return None


def clean_string(string: str):
    """Remove any class, percentage, or other details in parentheses from the provided string."""
    return re.sub(r'\s*\(.*?\)|\s*Class\s+[A-Z]|\s*\d+(\.\d+)?%', '', string).strip()


class ExtraETFParser:
    def __init__(self, ISIN):
        """
        Initialise the ExtraETF website parser for a specific ISIN number.
        """
        self.ISIN = ISIN
        self.url = "https://extraetf.com/de/"
        self.parsed_data = {}
        self.name = None
        self.invest_type = None

        response = self._try_fetch()

        if response and response.status_code == 200:
            self._parse_data(html_content=response.text)
        else:
            logger.warning(
                f"Failed to retrieve the webpage for '{self.ISIN}'.\n"
                f"Skipping this investment!"
            )

    def _try_fetch(self):
        """Attempt to fetch data from the various URL options.
        """
        logger.info("===== ATTEMPT PARSING FOR " + self.ISIN + " =====")

        # mimic a user-agent to avoid 403 error (website blocking access)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/85.0.4183.102 Safari/537.36"
        }

        for self.invest_type in INVEST_TYPES:
            self.url = f"https://extraetf.com/de/{self.invest_type}-profile/{self.ISIN}?tab=components"
            response = requests.get(self.url, headers=headers)
            if response.status_code == 200:
                return response

        return None

    def _parse_data(self, html_content):
        """Parse data for all the CATEGORIES from the HTML soup.
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.name = self.soup.find("h1").get_text(strip=True)

        logger.info("===== PARSING DATA FOR " + self.name + " =====")
        self.parsed_data = dict.fromkeys(CATEGORIES, {})
        self.parsed_data["ISIN"] = self.ISIN

        if self.invest_type == "stock":
            self.get_stock_data()

        else:
            for category, t in TAGS.items():

                if t['type'] == "tag":
                    self.parsed_data[category] = self.get_tag_data(t['name'])

                elif t['type'] == "notag":
                    self.parsed_data[category] = self.get_notag_data(t['name'], category=category)

                else:
                    raise ValueError(
                        f"Tag type '{t['type']}' for tag '{t['name']}' "
                        f"in category '{category}' is invalid!"
                    )

        logger.debug(
            "Parsed data for: '" + self.name + "'\n" +
            "\n".join(f"{c}: {d}" for c, d in self.parsed_data.items())
        )
        logger.info("==============================================")

    def get_tag_data(self, tag: str="app-top-holdings"):
        """
        Parse data from HTML soup that is findable directly via its tag
        """
        tag_data = {}

        # Find the section by its HTML tag
        section = self.soup.find(tag)

        if section:
            table = section.find('table')

            if table:
                logger.info(f"Tagged section '{tag}' found!")

                # Extract rows of data
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    cells = [cell.get_text(strip=True, separator="\n").split('\n')[0] for cell in row.find_all('td')]
                    cells = [c for c in cells if c]     # keep only actual values

                    cells[0] = str_to_float(cells[0])   # ranking of top holder
                    cells[-1] = str_to_float(cells[-1])     # percentage
                    # clean up the name of the top holding
                    name = clean_string(cells[1])
                    # save name with percentage
                    tag_data[name] = cells[-1]

                logger.debug(tag_data)

            else:
                logger.warning(
                    f"No table found in the {tag} component."
                )
        else:
            logger.warning(
                f"No tagged section by the name '{tag}' found."
            )

        return tag_data

    def get_notag_data(self, name: str, category: str):
        """
        Parse data from HTML soup that is in the general body
        and not findable directly via tag
        """
        nontag_data = {}

        # Find all instances of 'app-top-data-table'
        top_data_tables = self.soup.find_all('app-top-data-table')

        section = None
        for table in top_data_tables:
            header = table.find('h2', class_='card-title')
            if header and name in header.get_text():
                section = table
                break

        if section:
            logger.info(f"Section '{name}' found!")
            # Extract the relevant data
            data = section.find_all('div', class_='item ng-star-inserted')
            for allocation in data:
                key = allocation.find('span').text
                value = allocation.find('div', class_='value-block').text.strip()

                # replace key with the official German country name to ensure consistency
                if category == "countries":
                    key = get_official_country_name(key)

                nontag_data[key] = str_to_float(value)

            logger.debug(nontag_data)

        else:
            logger.warning(
                f"No section by the name '{name}' found in the 'app-top-data-table'."
            )

        return nontag_data


    def get_stock_data(self):
        """
        Parse data from HTML soup specifically for stock information,
        which is structured differently to etfs and fonds.
        """
        # Find the div with class 'profile-main-info separated-properties with-bottom-space'
        profile_info = self.soup.find("div", {"class": "profile-main-info separated-properties with-bottom-space"})

        # Extract country from the img tag within the profile_info_div
        country_img = profile_info.find("img", {"src": lambda x: x and "country" in x,
                                                "alt": True}) if profile_info else None
        countries = get_official_country_name(country_img["alt"]) if country_img else None

        # Get region from country, as it this info isn't included on the website
        country_ID = Path(country_img["src"]).stem if country_img else None
        regions = get_continent(country_ID)

        # Extract industry from the img tag within the profile_info_div
        industry_img = profile_info.find("img", {"src": lambda x: x and "branch" in x,
                                                 "alt": True}) if profile_info else None
        industries = industry_img["alt"] if industry_img else None

        # Extract company name
        name_tag = self.soup.find("h1")
        top_holdings = ''.join([
            text for text in name_tag.contents if isinstance(text, str)
        ]).strip() if name_tag else None

        for category in CATEGORIES:
            self.parsed_data[category] = {locals()[category]: 100.0}

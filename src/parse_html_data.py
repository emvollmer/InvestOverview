import logging
import requests
from bs4 import BeautifulSoup

from src.utils import setup_logging, CATEGORIES, TAGS, INVEST_TYPES

setup_logging()
logger = logging.getLogger(__name__)


def str_to_float(string: str):
    string = string.replace('\xa0%', '')
    string = string.replace(',', '.')

    return float(string)


class ExtraETFParser:
    def __init__(self, ISIN):
        self.ISIN = ISIN
        self.url = "https://extraetf.com/de/"
        self.parsed_data = {}
        self.name = None

        response = self._try_fetch()

        if response and response.status_code == 200:
            self._parse_data(html_content=response.text)
        else:
            logger.warning(
                f"Failed to retrieve the webpage for '{self.ISIN}'.\n"
                f"Skipping this investment!"
            )

    def _try_fetch(self):
        """Attempt to fetch from the various URL options.
        """
        logger.info("===== ATTEMPT PARSING FOR " + self.ISIN + " =====")

        # mimic a user-agent to avoid 403 error (website blocking access)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/85.0.4183.102 Safari/537.36"
        }

        for t in INVEST_TYPES:
            self.url = f"https://extraetf.com/de/{t}-profile/{self.ISIN}?tab=components"
            response = requests.get(self.url, headers=headers)
            if response.status_code == 200:
                return response

        return None

    def _parse_data(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.name = self.soup.find("h1").get_text(strip=True)

        logger.info("===== PARSING DATA FOR " + self.name + " =====")
        self.parsed_data = dict.fromkeys(CATEGORIES, {})
        self.parsed_data["ISIN"] = self.ISIN

        for category, t in TAGS.items():

            if t['type'] == "tag":
                self.parsed_data[category] = self.get_tag_data(t['name'])

            elif t['type'] == "notag":
                self.parsed_data[category] = self.get_notag_data(t['name'])

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
        Parse Data from HTML soup that is findable directly via its tag
        """
        tag_data = {}

        # Find the section by its HTML tag
        section = self.soup.find(tag)

        if section:
            table = section.find('table')
            
            if table:
                logger.info(f"Tagged section '{tag}' found!")
                # Extract headers
                headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
                
                # Extract rows of data
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    cells = [cell.get_text(strip=True) for cell in row.find_all('td')]
                    cells = [c for c in cells if c]     # keep only actual values

                    cells[0] = str_to_float(cells[0])
                    cells[-1] = str_to_float(cells[-1])
                    # save cells[1] = name of top holding, cells[-1] = percentage
                    tag_data[cells[1]] = cells[-1]

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

    def get_notag_data(self, name: str):
        """
        Parse Data from HTML soup that is in the general body
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
                nontag_data[key] = str_to_float(value)

            logger.debug(nontag_data)

        else:
            logger.warning(
                f"No section by the name '{name}' found in the 'app-top-data-table'."
            )

        return nontag_data

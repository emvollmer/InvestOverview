"""
Utilities functions and definitions
"""
import json
import logging
from pathlib import Path
from typing import Union

TAGS = {
    "top_holdings": {'type': 'tag', 'name': 'app-top-holdings'},
    "countries": {'type': 'notag', 'name': 'Länder-Allokation'},
    "industries": {'type': 'notag', 'name': 'Branchen'},
    "regions": {'type': 'notag', 'name': 'Regionen'}
}
CATEGORIES = list(TAGS.keys())
INVEST_TYPES = ["etf", "fund", "stock"]

CONTINENT_MAPPING = {
    "North America": "Nordamerika",
    "Europe": "Europa",
    "Asia": "Asien",
    "Oceania": "Pazifik",
    "South America": "Lateinamerika",
    "Eastern Europe": "Osteuropa",
    "Africa": "Afrika"
}

SRC_DIR = Path(__file__).parent
CONFIG_PATH = Path(SRC_DIR, 'config.json')
BASE_DIR = SRC_DIR.parent


def check_file(path: Union[Path, str]):
    """Check if path exists"""
    if not Path(path).is_file():
        raise FileNotFoundError(
            f"File does not exist at {path}!"
        )


def read_config():
    """Read the config.json"""
    check_file(CONFIG_PATH)
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def get_excel_path():
    """Get the excel_path from the config.json,
    unless that path hasn't yet been properly defined and
    a single portfolio xlsx or xlsm file exists in the dir tree.
    """
    config = read_config()
    excel_path = Path(config["excel_path"])

    if not excel_path.exists():
        potential_paths = (sorted(BASE_DIR.rglob("*portfolio*.xlsx")) +
                           sorted(BASE_DIR.rglob("*portfolio*.xlsm")))
        if len(potential_paths) == 1:
            excel_path = potential_paths[0]

    return str(excel_path)


def update_config(excel_path: Union[Path, str]):
    """Save the new excel_path to the config.json."""
    config = read_config()
    config["excel_path"] = str(excel_path)

    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        format="{asctime} - {name} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )

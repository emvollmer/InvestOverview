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

SRC_DIR = Path(__file__).parent
CONFIG_PATH = Path(SRC_DIR, 'config.json')


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
    """Get the excel_path from the config.json"""
    config = read_config()
    return config["excel_path"]


def update_config(excel_path: Union[Path, str]):
    """Save the new excel_path to the config.json"""
    config = read_config()
    config["excel_path"] = str(excel_path)

    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)


def setup_logging():
    logging.basicConfig(
        format="{asctime} - {name} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )

import argparse
import logging
from csv import excel
from pathlib import Path

import src.utils as ut
from src.excel_worker import ExcelWorker
from src.parse_html_data import ExtraETFParser

EXCEL_PATH = ut.get_excel_path()
ut.setup_logging()
logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process some inputs for Excel path.")
    parser.add_argument('--excel_path', type=str,
                        help=f'Path to the Excel file. Default (from config.json): "{EXCEL_PATH}"',
                        default=EXCEL_PATH)
    return parser.parse_args()


def main(
        xlsx_path: str = EXCEL_PATH
):
    xlsx_path = Path(xlsx_path)
    # xlsx_path = Path("C:/Users/EV/Documents/Finance meetings/2024-08-25_Portfolio_testing3.xlsx")

    ut.check_file(xlsx_path)
    if xlsx_path is not EXCEL_PATH:
        logging.info(f"Updating config.json with provided excel path: {xlsx_path}")
        ut.update_config(xlsx_path)

    # Extract investment information from Excel file
    excel = ExcelWorker(xlsx_path)
    investments = excel.get_investments()

    parsed_invest_data = {}

    for isin, euro in investments:
        etf = ExtraETFParser(isin)
        if etf.name:
            parsed_invest_data[etf.name] = etf.parsed_data

    # Update investment percentages according to planned amounts
    updated_parsed_invest_data = adjust_parsed_investment_percentages(
        investments=investments,
        parsed_etf_data=parsed_invest_data
    )
    excel.write_overview(updated_parsed_invest_data)


def adjust_parsed_investment_percentages(
        investments: list,
        parsed_etf_data: dict
):
    """
    Adjusts the percentages in parsed_invest_data based on the amount
    of money planned to be invested.

    :param investments: List of tuples where each tuple
        contains an ISIN and amount.
    :param parsed_etf_data: Dict containing parsed investment data.
    :return: Updated parsed_invest_data with adjusted percentages.
    """
    # Update investments to reflect only those ETFs that can be found online
    found_ETFs = [d['ISIN'] for d in parsed_etf_data.values()]
    updated_investments = [i for i in investments if i[0] in found_ETFs]

    total_amount = sum(amount for _, amount in updated_investments)
    logger.info(f"Total invested amount: {round(total_amount,2)} €")

    investments_weighted = {
        isin: amount / total_amount
        for isin, amount in dict(updated_investments).items()
    }
    logger.info(
        "Investments weighted according to total amount:\n" +
        "\n".join(f"{isin}: {v:.2%}" for isin, v in investments_weighted.items())
    )

    # Adjust percentages for each ETF
    updated_parsed_etf_data = {
        etf_name: {c: {} for c in ut.CATEGORIES}
        for etf_name in parsed_etf_data.keys()
    }

    for etf_name, etf_data in parsed_etf_data.items():

        weight = investments_weighted[etf_data['ISIN']]

        for c in ut.CATEGORIES:
            updated_parsed_etf_data[etf_name][c] = {
                key: value * weight
                for key, value in etf_data[c].items()
            }

    logger.debug(
        "Updated parsed data:\n" +
        "\n".join(f"{c}:\n\t{d}" for c, d in updated_parsed_etf_data.items())
    )
    return updated_parsed_etf_data


if __name__ == "__main__":
    args = parse_arguments()
    main(args.excel_path)

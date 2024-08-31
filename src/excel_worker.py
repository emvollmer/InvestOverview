from pathlib import Path
import pandas as pd
import logging

from src.utils import CATEGORIES, setup_logging, check_file

setup_logging()
logger = logging.getLogger(__name__)


class ExcelWorker:
    def __init__(self, excel_path: Path):
        self.excel_path = Path(excel_path)
        check_file(self.excel_path)

        if not self.excel_path.suffix == ".xlsx":
            raise ValueError(
                f"The provided file '{self.excel_path}' is not an excel!"
            )

    def get_investments(self):
        """
        Get list of investments according to their ISIN number and
        the invested in euro
        :param df: dataframe
        :return: list of (ISIN, euro amount) values
        """
        df = pd.read_excel(self.excel_path)

        # get ISIN column
        try:
            isin_loc = df[df.isin(['ISIN'])].stack().idxmax()   # returns: (row, col)
            starting_row = isin_loc[0]
            isin_col = df.columns.get_loc(isin_loc[1])
        except IndexError as e:
            raise ValueError(
                f"No cell 'ISIN' in excel file! ISIN numbers are required "
                f"to extract ETF information. Please provide them under a "
                f"labelled column header"
            ) from e

        # get invested amounts column
        euro_col = find_column(df, starting_row)

        # get values
        isin_values = df.iloc[starting_row + 1:, isin_col]
        euro_values = df.iloc[starting_row + 1:, euro_col]
        investments = [
            (isin, euro if pd.notna(euro) else 0)
            for isin, euro in zip(isin_values, euro_values)
            if pd.notna(isin)
        ]

        logger.info(
            f"Investments:\n{chr(10).join(map(str, investments))}"
        )
        return investments

    def write_overview(self, parsed_invest_data: dict):
        combined_data = {c: {} for c in CATEGORIES}

        # populate the combined_data dictionary
        for etf, data in parsed_invest_data.items():
            for category in CATEGORIES:
                df = pd.DataFrame(
                    list(data[category].items()),
                    columns=[category.capitalize(), 'Percentage']
                )
                combined_data[category][etf] = df.set_index(
                    category.capitalize()
                ).rename(columns={'Percentage': etf})

        # combine dataframes into a single dataframe for each category
        final_data = {}
        for category, dfs in combined_data.items():
            combined_df = pd.concat(dfs.values(), axis=1, join='outer').reset_index()

            # Calculate the overall percentage for each row
            combined_df['Overall Percentage'] = combined_df.iloc[:, 1:].sum(axis=1)
            total_sum = combined_df['Overall Percentage'].sum()
            combined_df['Overall Percentage'] = (
                    (combined_df['Overall Percentage'] / total_sum) * 100
            )

            # insert 'Overall Percentage' as the second column (index 1)
            cols = combined_df.columns.tolist()
            cols.insert(1, cols.pop(cols.index('Overall Percentage')))
            combined_df = combined_df[cols]

            # sort the dataframe by 'Overall Percentage' in descending order
            combined_df = combined_df.sort_values(
                by='Overall Percentage', ascending=False
            )

            final_data[category] = combined_df

        # write content of the dataframes to individual sheets in a different Excel file
        mode = "a"
        dst_excel_path = Path(self.excel_path.parent, "_investment_overview_python.xlsx")
        if not dst_excel_path.is_file():
            mode = "w"

        try:
            with pd.ExcelWriter(
                    dst_excel_path, engine='openpyxl', mode=mode,
                    if_sheet_exists='replace' if mode == 'a' else None
            ) as writer:
                for category, df in final_data.items():
                    df.to_excel(writer, sheet_name=category.capitalize(), index=False)

        except PermissionError:
            raise PermissionError(
                f"Excel file '{dst_excel_path}' seems to be open. "
                f"Has to be closed before new data can be saved!"
            )


def find_column(
        df: pd.DataFrame,
        row: int,
        keywords: list = ("€", "euro", "amount")
):
    """
    Find the cell in a row that matches one of the keywords.

    :param df: dataframe of Excel data
    :param row: row that is being searched
    :param keywords: list of keywords to find a matching cell for
    :return: column number of the identified, matching cell
    :raise ValueError, if no match was found
    """
    for keyword in keywords:
        matching_columns = df.columns[
            df.iloc[row].str.contains(keyword, case=False, na=False)
        ]
        if not matching_columns.empty:
            return df.columns.get_loc(matching_columns[0])

    raise ValueError(
        f"No cell found in the excel row {row+2}, "
        f"that matches any of the keywords {keywords}!"
    )

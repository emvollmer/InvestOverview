# Invest Overview

This repo helps provide an overview of your financial portfolio, specifically 
the total distribution across countries, regions, industries,
and top holdings.

It requires your financial information to be placed in a `.xlsx` or `.xlsm` file,
similarly structured to the example provided in `examples/example_portfolio.xlsm`.
Utilising this data, the code will extract information
from [https://extraetf.com/de/](https://extraetf.com/de/) and concatenate it to
calculate the distribution overviews, which can be visualised as f.e. pie charts
in your Excel portfolio.

## Installation and Usage

While the code can be run directly via CL, the most efficient way is use it
is via a `.exe` file in combination with an excel VBA macro button, as
demonstrated in the `example_portfolio.xlsm`. This requires the following:

1. Download the `examples/example_portfolio.xlsm` file, place it in your folder of
choice and amend according to your personal investment plan.

2. If not available, build the `.exe` with:
```bash
pip install pyinstaller
pyinstaller InvestOverview.spec
```
> **Note:** This code was developed in Windows 10, so the `.spec` and any `.exe` are
> designed for the Windows OS. Building the `.exe` from the `.spec` in other OSs
> may work, but hasn't been tested.

3. Place the `InvestOverview.exe` file into the folder containing your `portfolio.xlsm`.

You can now press the button in the `portfolio.xlsm` to execute the VBA macro and
update the pie charts with current information. The calculated values will be saved
to a separate excel `_investment_overview_python.xlsx` file.

> **Note:** A time limit of 5 minutes is currently placed on button execution.
> If your internet connection is very slow or your number of investments very
> large this may cause `PermissionDeniedErrors` during execution.
> It will be necessary to amend the line in question your button macro
> (see `vba/RunInvestOverview.bas`).

### Direct Usage

If you prefer to work without macros, you can also get the `_investment_overview_python.xlsx`
by running the code directly. This is possible in the two following ways.

- Run the `.exe` can also be run directly from the terminal with:
```bash
InvestOverview.exe --excel_path "C:\\path\\to\\your\\portfolio.xlsx"
```
- Run the code as such directly via CL by first installing all required packages
before calling the module:
```bash
# Note: The code was developed with python 3.12
pip install -r requiremnts.txt
python -m src.invest_overview --excel_path "C:\\path\\to\\your\\portfolio.xlsx"
```
> **Note:** The `--excel_path` flag is only necessary if there is no single `.xlsx` or `.xlsm`
> file in directory tree. For example, by default, the `excel_path` of this repository
> will be `examples/example_portfolio.xlsm`. Run `python -m src.invest_overview --help` for
> details.
> 
> The `config.json` is updated with any path provided via `--excel_path`, so it suffices to add
> the path only in the first call.

## Structure
```
InvestOverview/
│
├── examples/           ---> example files
│   └── example_portfolio.xlsm  ---> example excel to showcase button and .exe use
│
├── src/                ---> python code
│   ├── __init__.py
│   ├── config.json             ---> contains excel path definition
│   ├── excel_worker.py         ---> read / write to excel
│   ├── invest_overview.py      ---> main module which coordinates code
│   ├── parse_html_data.py      ---> get data from internet
│   └── utils.py                ---> utility functions
│
├── vba/                ---> excel code
│   └── RunInvestOverview.bas   ---> macro code for button, as included in `example_portfolio.xlsm`
│
├── InvestOverview.spec ---> spec file with which to build .exe
├── README.md           ---> this file
└── requirements.txt    ---> requirements file of package versions
```

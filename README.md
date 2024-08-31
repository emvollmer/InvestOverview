# Invest Overview

This repo helps provide an overview of your financial portfolio, specifically 
the total distribution across countries, regions, industries
and more.

It requires your financial information to be placed in a `.xlsx` file
with a column headed `ISIN` containing info on the ETFs, fonds or stocks
in question and one headed `amount` or `euro` with the planned or current
investment amounts. Utilising this data, the code will extract information
from [https://extraetf.com/de/](https://extraetf.com/de/) and concatenates it.

## Structure
```
InvestOverview/
├── src/
│   ├── __init__.py
│   ├── config.json
│   ├── excel_worker.py
│   ├── invest_overview.py
│   ├── parse_html_data.py
│   └── utils.py
│
├── InvestOverview.spec
├── README.md
└── requirements.txt
```

## Building the .exe

To build the executable from the `.spec` file, it's necessary to do:

```bash
pip install pyinstaller
pyinstaller InvestOverview.spec
```

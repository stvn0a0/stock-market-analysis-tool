# Stock Market Analysis Tool

This repository contains simple utilities for downloading historical stock
prices and computing common technical indicators. It relies on the
[yfinance](https://github.com/ranaroussi/yfinance) package to access data
from Yahoo Finance.

## Features

- Download historical OHLC data for a given ticker
- Compute 20 and 50 day simple moving averages
- Calculate Bollinger Bands
- Compute the Relative Strength Index (RSI)
- Calculate MACD and signal lines
- Basic command line interface for quick analysis

## Requirements

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the analysis script from the command line. The following example fetches
data for Apple (AAPL) between January and December 2023 and prints the latest
rows including indicators. You can also compute a short-term score (1-100)
combining several technical and fundamental metrics:

```bash
python stock_analysis.py AAPL --start 2023-01-01 --end 2023-12-31

# save results to CSV
python stock_analysis.py AAPL --start 2023-01-01 --end 2023-12-31 --csv aapl.csv

# print short-term score
python stock_analysis.py AAPL --start 2023-01-01 --end 2023-12-31 --score
```

The module can also be imported in your own scripts to fetch data and compute
indicators programmatically.

## License

This project is released under the terms of the MIT License.

# Stock Market Analysis Tool

This repository contains a suite of tools for downloading historical stock data and computing popular technical indicators. Data is now fetched using the [yfinance](https://pypi.org/project/yfinance/) library (see note below).

**Note:** If you previously used the Polygon.io API, this tool now uses the yfinance library by default (verify the latest `requirements.txt`).

## Features

* Download historical OHLC data for a given ticker
* Compute 20-day and 50-day simple moving averages
* Calculate Bollinger Bands
* Compute the Relative Strength Index (RSI)
* Calculate the Moving Average Convergence Divergence (MACD) and signal lines
* Batch processing of multiple tickers with optional scoring
* Command-line interface for quick analysis

## Requirements

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

The current requirements include:

* pandas
* numpy
* matplotlib
* yfinance

## Usage

Run the analysis script from the command line. The following example fetches
data for Apple (AAPL) between January and December 2023 and prints the latest
rows including indicators:

```bash
python stock_analysis.py AAPL --start 2023-01-01 --end 2023-12-31
```

Save results to a CSV file:

```bash
python stock_analysis.py AAPL --start 2023-01-01 --end 2023-12-31 --csv aapl.csv
```

Print a short-term score (1–100) combining several technical and fundamental metrics:

```bash
python stock_analysis.py AAPL --start 2023-01-01 --end 2023-12-31 --score
```

You can also analyze multiple tickers using the batch scoring utility:

```bash
python batch_score.py tickers.txt
```

Where `tickers.txt` contains a list of tickers (one per line).

The module can also be imported into your own scripts to fetch data and compute indicators programmatically.

## License

This project is released under the terms of the MIT License.


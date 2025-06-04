"""Utilities for downloading stock data and computing indicators."""

from __future__ import annotations

import pandas as pd
import yfinance as yf


class DownloadError(Exception):
    """Raised when data download fails."""
    pass


def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download historical OHLC data for a ticker between dates."""
    try:
        df = yf.download(ticker, start=start, end=end)
    except Exception as exc:
        raise DownloadError(f"Failed to download data for {ticker}: {exc}") from exc

    if df.empty:
        raise DownloadError(f"No data returned for {ticker}. Check ticker symbol or network access.")

    df.index.name = "Date"
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common technical indicators to the dataframe."""
    # Simple moving averages
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()

    # Bollinger Bands (20 day window, 2 std)
    rolling_mean = df["Close"].rolling(window=20).mean()
    rolling_std = df["Close"].rolling(window=20).std()
    df["BB_upper"] = rolling_mean + (rolling_std * 2)
    df["BB_lower"] = rolling_mean - (rolling_std * 2)

    # Relative Strength Index (RSI)
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Moving Average Convergence Divergence (MACD)
    short_ema = df["Close"].ewm(span=12, adjust=False).mean()
    long_ema = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = short_ema - long_ema
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    return df


def analyze_ticker(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Convenience function to download data and compute indicators."""
    df = fetch_data(ticker, start, end)
    return calculate_indicators(df)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple stock analysis")
    parser.add_argument("ticker", help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--start", default="2023-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2023-12-31", help="End date YYYY-MM-DD")
    parser.add_argument("--csv", help="Optional path to save results as CSV")
    args = parser.parse_args()

    try:
        data = analyze_ticker(args.ticker, start=args.start, end=args.end)
    except DownloadError as exc:
        parser.error(str(exc))

    if args.csv:
        data.to_csv(args.csv)
        print(f"Results saved to {args.csv}")
    else:
        print(data.tail())

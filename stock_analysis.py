"""Utilities for downloading stock data and computing indicators."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
from polygon import RESTClient


class DownloadError(Exception):
    """Raised when data download fails."""
    pass


def fetch_data(ticker: str, start: str, end: str, api_key: Optional[str] = None) -> pd.DataFrame:
    """Download historical OHLC data for a ticker between dates using Polygon."""
    key = api_key or os.getenv("POLYGON_API_KEY")
    client = RESTClient(key)

    try:
        aggs = client.get_aggs(ticker, 1, "day", start, end, limit=50000)
    except Exception as exc:
        raise DownloadError(f"Failed to download data for {ticker}: {exc}") from exc

    if not aggs:
        raise DownloadError(
            f"No data returned for {ticker}. Check ticker symbol or network access."
        )

    rows = [
        {
            "Date": datetime.fromtimestamp(a.timestamp / 1000.0),
            "Open": a.open,
            "High": a.high,
            "Low": a.low,
            "Close": a.close,
            "Volume": a.volume,
        }
        for a in aggs
    ]
    df = pd.DataFrame(rows).set_index("Date")
    df.index = pd.to_datetime(df.index)
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


def fetch_fundamentals(ticker: str) -> Dict[str, float]:
    """Return a dictionary with basic fundamental metrics using Polygon.

    The Polygon API does not currently expose all of the fundamental fields
    used by :func:`compute_score`, so this function returns an empty dictionary
    as a placeholder. Implementations that require fundamental data should query
    the appropriate Polygon endpoints and populate the returned mapping.
    """

    _ = ticker  # unused for now
    return {}


def compute_score(df: pd.DataFrame, fundamentals: Dict[str, float]) -> float:
    """Compute a simple 1-100 short-term score using technical and fundamental data."""
    # Technical scores
    latest = df.iloc[-1]
    score = 0.0

    rsi = latest.get("RSI", 50)
    if rsi < 30:
        score += 15
    elif rsi > 70:
        score += 0
    else:
        score += 7.5

    macd = latest.get("MACD", 0)
    macd_signal = latest.get("MACD_signal", 0)
    if macd > macd_signal:
        score += 20

    close = latest.get("Close")
    bb_upper = latest.get("BB_upper")
    bb_lower = latest.get("BB_lower")
    if close is not None and bb_lower is not None and close <= bb_lower:
        score += 10
    elif close is not None and bb_upper is not None and close >= bb_upper:
        score += 0
    else:
        score += 5

    sma20 = latest.get("SMA_20")
    sma50 = latest.get("SMA_50")
    if close is not None and sma20 is not None and close > sma20:
        score += 7
    if close is not None and sma50 is not None and close > sma50:
        score += 8
    if sma20 is not None and sma50 is not None and sma20 > sma50:
        score += 0

    # Fundamental scores
    pe = fundamentals.get("trailingPE")
    if pe is not None:
        if pe < 15:
            score += 10
        elif pe <= 25:
            score += 5

    eg = fundamentals.get("earningsQuarterlyGrowth")
    if eg is not None:
        if eg > 0.2:
            score += 15
        elif eg > 0.1:
            score += 10
        elif eg > 0:
            score += 5

    de_ratio = fundamentals.get("debtToEquity")
    if de_ratio is not None:
        if de_ratio < 100:
            score += 5
        elif de_ratio < 200:
            score += 2.5

    rev_growth = fundamentals.get("revenueQuarterlyGrowth")
    if rev_growth is not None:
        if rev_growth > 0.1:
            score += 10
        elif rev_growth > 0:
            score += 5

    # Bound score between 0 and 100
    return max(0.0, min(100.0, score))


def score_ticker(ticker: str, start: str, end: str) -> float:
    """Convenience helper to analyze a ticker and return its score."""
    df = analyze_ticker(ticker, start, end)
    fundamentals = fetch_fundamentals(ticker)
    return compute_score(df, fundamentals)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple stock analysis")
    parser.add_argument("ticker", help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--start", default="2023-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2023-12-31", help="End date YYYY-MM-DD")
    parser.add_argument("--csv", help="Optional path to save results as CSV")
    parser.add_argument(
        "--score",
        action="store_true",
        help="Print 1-100 short-term score based on technicals and fundamentals",
    )
    args = parser.parse_args()

    try:
        data = analyze_ticker(args.ticker, start=args.start, end=args.end)
    except DownloadError as exc:
        parser.error(str(exc))

    if args.score:
        try:
            score = score_ticker(args.ticker, args.start, args.end)
            print(f"Short-term score: {score:.1f}/100")
        except DownloadError as exc:
            parser.error(str(exc))

    if args.csv:
        data.to_csv(args.csv)
        print(f"Results saved to {args.csv}")
    else:
        print(data.tail())

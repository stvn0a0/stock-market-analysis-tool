#!/usr/bin/env python3
"""Utilities for downloading stock data and computing both 5-day and 20-day scores using yfinance."""

from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf
from functools import lru_cache
from typing import Dict
from datetime import datetime

class DownloadError(Exception):
    """Raised when data download fails."""
    pass

def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False
    )
    if df.empty:
        raise DownloadError(f"No data returned for {ticker}.")
    # — If yfinance gave you a MultiIndex (variable, ticker), drop the ticker level:
    if isinstance(df.columns, pd.MultiIndex):
        # level 0 is the OHLCV+indicator names, level 1 is the ticker
        df.columns = df.columns.droplevel(1)
    df = df.rename_axis("Date").loc[:, ["Open","High","Low","Close","Volume"]]
    df.index = pd.to_datetime(df.index)
    return df


def calculate_indicators(
    df: pd.DataFrame,
    sma_short: int,
    sma_long: int,
    bb_window: int,
    rsi_window: int,
    macd_fast: int,
    macd_slow: int,
    macd_signal: int,
) -> pd.DataFrame:
    df = df.copy()

    # Moving averages
    df["SMA_short"] = df["Close"].rolling(window=sma_short).mean()
    df["SMA_long"]  = df["Close"].rolling(window=sma_long).mean()

    # Bollinger Bands
    m = df["Close"].rolling(window=bb_window).mean()
    s = df["Close"].rolling(window=bb_window).std()
    df["BB_upper"] = m + 2 * s
    df["BB_lower"] = m - 2 * s

    # ATR
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"]  - df["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(window=bb_window).mean()

    # ADX
    high_diff = df["High"].diff()
    low_diff  = df["Low"].diff()
    plus_dm   = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0.0)
    minus_dm  = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0.0)

    atr = df["ATR"]
    plus_di  = 100 * plus_dm.ewm(span=bb_window, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(span=bb_window, adjust=False).mean() / atr
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)

    adx = dx.ewm(span=bb_window, adjust=False).mean()
    # if it's ever a 1-col DataFrame, pull out that column
    if isinstance(adx, pd.DataFrame):
        adx = adx.iloc[:, 0]
    df["ADX"] = adx

    # RSI
    delta = df["Close"].diff()
    gain  = delta.where(delta > 0, 0).rolling(window=rsi_window).mean()
    loss  = -delta.where(delta < 0, 0).rolling(window=rsi_window).mean()
    df["RSI"] = 100 - (100 / (1 + gain / loss))

    # MACD
    fast = df["Close"].ewm(span=macd_fast, adjust=False).mean()
    slow = df["Close"].ewm(span=macd_slow, adjust=False).mean()
    df["MACD"]        = fast - slow
    df["MACD_signal"] = df["MACD"].ewm(span=macd_signal, adjust=False).mean()

    # OBV
    df["OBV"] = (np.sign(df["Close"].diff().fillna(0)) * df["Volume"]).cumsum()

    return df

@lru_cache(maxsize=None)
def fetch_fundamentals(ticker: str) -> Dict[str, float]:
    t    = yf.Ticker(ticker)
    info = t.info or {}
    out: Dict[str, float] = {}
    if (pe := info.get("trailingPE")) is not None:
        out["trailingPE"] = float(pe)
    if (eg := info.get("earningsQuarterlyGrowth")) is not None:
        out["earningsQuarterlyGrowth"] = float(eg)
    if (rg := info.get("revenueQuarterlyGrowth") or info.get("quarterlyRevenueGrowth")) is not None:
        out["revenueQuarterlyGrowth"] = float(rg)
    if (de := info.get("debtToEquity")) is not None:
        out["debtToEquity"] = float(de)
    return out

def compute_score(
    df: pd.DataFrame,
    fundamentals: Dict[str, float],
    lookback_days: int
) -> float:
    score = 0.0
    '''
    latest = df.iloc[-1]
    window = df.iloc[-lookback_days:]
    '''

    # RSI: mean over lookback
    rsi_series = df["RSI"].tail(lookback_days).dropna()
    if not rsi_series.empty:
        rsi_mean = rsi_series.mean()
        score   += 15 * (1 - abs(rsi_mean - 50) / 50)

    # MACD histogram
    hist = (df["MACD"] - df["MACD_signal"]).dropna()
    if len(hist) >= lookback_days:
        hist_latest = hist.iloc[-1]
        roll_mean   = hist.abs().rolling(window=lookback_days).mean().dropna()
        if not roll_mean.empty:
            avg_hist = roll_mean.iloc[-1]
            if avg_hist != 0:
                score += 20 * (hist_latest / avg_hist)

    # Bollinger position
    c  = df["Close"].iat[-1]
    bu = df["BB_upper"].iat[-1]
    bl = df["BB_lower"].iat[-1]
    if (not np.isnan(bu)) and (not np.isnan(bl)) and (bu > bl):
        frac = (c - bl) / (bu - bl)
        frac = min(max(frac, 0.0), 1.0)
        score += 10 * (1 - frac)

    # SMA cross & position
    sma_s = df["SMA_short"].iat[-1]
    sma_l = df["SMA_long"].iat[-1]
    # now sma_s and sma_l are numpy floats, so no more ambiguous truth
    if not np.isnan(sma_s):
        score += 5 * ((c / sma_s) - 1)
    if not np.isnan(sma_l):
        score += 5 * ((c / sma_l) - 1)
    if (not np.isnan(sma_s)) and (not np.isnan(sma_l)):
        score += 5 if sma_s > sma_l else -5

    # ATR volatility
    atr = df["ATR"].iat[-1]
    if (not np.isnan(atr)) and atr > 0:
        ratio = atr / c
        raw   = (0.04 - ratio) / 0.02
        score += max(0.0, min(1.0, raw)) * 5

    # ADX trend strength
    adx = df["ADX"].iat[-1]
    if not np.isnan(adx):
        score += (min(adx, 50) / 50) * 5

    # OBV confirmation
    if len(df) >= 2:
        obv_latest = df["OBV"].iat[-1]
        obv_prev   = df["OBV"].iat[-2]
        if obv_latest > obv_prev:
            score += 5

    # Fundamentals (interpolated + decayed)
    fs = 0.0
    pe  = fundamentals.get("trailingPE")
    eg  = fundamentals.get("earningsQuarterlyGrowth")
    de  = fundamentals.get("debtToEquity")
    rg  = fundamentals.get("revenueQuarterlyGrowth")

    if pe  is not None: fs += np.interp(pe,  [5,15,25,50], [10,10, 5, 0])
    if eg  is not None: fs += np.interp(eg,  [0,0.1,0.2,1],  [0, 5,15,15])
    if de  is not None: fs += np.interp(de,  [0,50,100,300],[5, 5,2.5,0])
    if rg  is not None: fs += np.interp(rg,  [0,0.1,0.5],   [0,10,10])

    decay = min(lookback_days / 20, 1.0)
    score += fs * decay

    return float(np.clip(score, 0, 100))

def analyze_and_score(
    ticker: str,
    as_of: datetime,
    lookback_days: int,
    params: dict,
) -> float:
    needed = max(params["sma_long"], params["bb_window"], params["rsi_window"], params["macd_slow"])
    days   = lookback_days + needed
    start  = (as_of - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    end    = as_of.strftime("%Y-%m-%d")

    df   = fetch_data(ticker, start, end)
    df   = calculate_indicators(df, **params)
    fund = fetch_fundamentals(ticker)
    return compute_score(df, fund, lookback_days)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Compute 5-day & 20-day scores")
    p.add_argument("ticker", help="Ticker symbol, e.g. AAPL")
    p.add_argument(
        "--as-of",
        default=datetime.today().strftime("%Y-%m-%d"),
        help="As-of date YYYY-MM-DD (default today)",
    )
    args  = p.parse_args()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d")

    params5 = {
        "sma_short": 3,  "sma_long": 5,
        "bb_window": 5,  "rsi_window": 5,
        "macd_fast": 3,  "macd_slow": 8, "macd_signal": 3,
    }
    params20 = {
        "sma_short": 10, "sma_long": 20,
        "bb_window": 20, "rsi_window": 14,
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
    }

    s5  = analyze_and_score(args.ticker, as_of, lookback_days=5,  params=params5)
    s20 = analyze_and_score(args.ticker, as_of, lookback_days=20, params=params20)
    print(f"5-day score  for {args.ticker} as of {args.as_of}: {s5:.1f}/100")
    print(f"20-day score for {args.ticker} as of {args.as_of}: {s20:.1f}/100")
# batch_score.py

import csv
import datetime
from stock_analysis import analyze_and_score

# 5-day and 20-day parameter sets (must match what's in stock_analysis.py)
params5 = {
    "sma_short": 3,  "sma_long": 5,
    "bb_window": 5,  "rsi_window": 5,
    "macd_fast": 3,  "macd_slow": 8,  "macd_signal": 3,
}
params20 = {
    "sma_short": 10, "sma_long": 20,
    "bb_window": 20, "rsi_window": 14,
    "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
}

def main():
    # as_of must be a datetime so that pd.Timedelta subtraction works
    as_of = datetime.datetime.today()

    # Load tickers
    with open('tickers.txt') as f:
        tickers = [line.strip() for line in f if line.strip()]

    results = []
    for ticker in tickers:
        try:
            score_5  = analyze_and_score(ticker, as_of, lookback_days=5,  params=params5)
            score_20 = analyze_and_score(ticker, as_of, lookback_days=20, params=params20)
            results.append({
                'ticker':    ticker,
                'score_5':   score_5,
                'score_20':  score_20,
            })
        except Exception as e:
            print(f"Error scoring {ticker}: {e}")

    # Dump everything to CSV
    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['ticker','score_5','score_20'])
        writer.writeheader()
        writer.writerows(results)

    # Print best performers if any succeeded
    if results:
        best_5  = max(results, key=lambda x: x['score_5'])
        best_20 = max(results, key=lambda x: x['score_20'])
        print(f"Best 5-day performer : {best_5['ticker']}  →  {best_5['score_5']:.1f}/100")
        print(f"Best 20-day performer: {best_20['ticker']}  →  {best_20['score_20']:.1f}/100")
    else:
        print("No tickers scored successfully. Check for errors above.")

if __name__ == "__main__":
    main()
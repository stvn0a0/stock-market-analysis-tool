import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from stock_analysis import fetch_data
 
ticker_symbol1 = 'TSLA'
ticker_symbol2 = 'AAPL'
start_date = '2023-01-01'
end_date = '2023-12-15'

stock_data1 = fetch_data(ticker_symbol1, start=start_date, end=end_date)
stock_data2 = fetch_data(ticker_symbol2, start=start_date, end=end_date)

#data inspection and cleaning
print(stock_data1.head())
#print(stock_data2.head())


#calculating indicators
#stock1
#20-day moving average
stock_data1['SMA_20'] = stock_data1['Close'].rolling(window=20).mean() 
#50-day moving average
stock_data1['SMA_50'] = stock_data1['Close'].rolling(window=50).mean()
"""
#stock2
#20-day moving average
stock_data2['SMA_20'] = stock_data2['Close'].rolling(window=20).mean() 
#50-day moving average
stock_data2['SMA_50'] = stock_data2['Close'].rolling(window=50).mean()
"""


#calculation of other technical indicators
#Relative Strength Index (RSI)
delta1 = stock_data1['Close'].diff()
gain1 = (delta1.where(delta1 > 0, 0)).rolling(window=14).mean()
loss1 = (-delta1.where(delta1 < 0, 0)).rolling(window=14).mean()
rs = gain1/loss1
stock_data1['RSI'] = 100 - (100 / (1 + rs))
print (stock_data1['RSI'].tail(10))

"""
#Moving Average Divergence (MACD)
short term exponential moving average (EMA)
#short_ema = stock_data1['Close'].ewm(span=12, adjust=False).mean()
long term exponential moving average (EMA)
#long_ema = stock_data1['Close'].ewm(span=26, adjust=False).mean()
"""


#data visualization
#comparitive analysis between different stock
#plt.figure(figsize=(12, 6))
#create subplots and share the x-axis
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
#Plotting the Closing Prices
#2 rows, 1 column, 1st subplot
"""
plt.subplot(2, 1, 1) 
plt.title(f'{ticker_symbol1} vs {ticker_symbol2} Stock Prices')
plt.xlabel('Date')
plt.ylabel('Close Price USD ($)')
plt.plot(stock_data1['Close'], label=f'{ticker_symbol1} Close Price')
#plt.plot(stock_data2['Close'], label=f'{ticker_symbol2} Close Price')
#plotting SMA
plt.plot(stock_data1['SMA_20'], label=f'20-day SMA for {ticker_symbol1}')
plt.plot(stock_data1['SMA_50'], label=f'50-day SMA for {ticker_symbol1}')

plt.plot(stock_data2['SMA_20'], label=f'20-day SMA for {ticker_symbol2}')
plt.plot(stock_data2['SMA_50'], label=f'50-day SMA for {ticker_symbol2}')
plt.legend()
"""
ax1.plot(stock_data1['Close'], label=f'{ticker_symbol1} Close Price')
ax1.set_title(f'{ticker_symbol1} vs {ticker_symbol2} Stock Prices')
#plotting SMA
ax1.plot(stock_data1['SMA_20'], label=f'20-day SMA for {ticker_symbol1}')
ax1.plot(stock_data1['SMA_50'], label=f'50-day SMA for {ticker_symbol1}')
ax1.set_xlabel('Date')
ax1.set_ylabel('Close Price USD ($)')
ax1.legend()
#Plotting the RSI
#2 rows, 1 column, 2nd subplot
"""
plt.subplot(2, 1, 2)
plt.plot(stock_data1['RSI'], label='RSI')
plt.title('Relative Strength Index (RSi)')
plt.legend()
"""
ax2.plot(stock_data1['RSI'], label='RSI', color = 'orange')
ax2.set_title('Relative Strength Index (RSI)')
ax1.set_xlabel('Date')
ax1.set_ylabel('RSI')
ax2.legend()
plt.tight_layout()
plt.show()



import yfinance as yf
import pandas as pd

# Download NIFTY 50 (^NSEI) daily data for the last 1 year
nifty = yf.download("^NSEI", start="2024-01-01", end="2025-01-01", interval="1d")

# Flatten columns if MultiIndex
if isinstance(nifty.columns, pd.MultiIndex):
    nifty.columns = ['_'.join(col).strip() for col in nifty.columns.values]

# Use the correct column name for Close
close_col = 'Close_^NSEI'

# Calculate 20-period SMA
nifty['SMA20'] = nifty[close_col].rolling(window=20).mean()

# Generate signals
nifty['Prev_Close'] = nifty[close_col].shift(1)
nifty['Prev_SMA20'] = nifty['SMA20'].shift(1)

# Buy: Close crosses above SMA20
nifty['Buy_Signal'] = (nifty['Prev_Close'] < nifty['Prev_SMA20']) & (nifty[close_col] > nifty['SMA20'])
# Sell: Close crosses below SMA20
nifty['Sell_Signal'] = (nifty['Prev_Close'] > nifty['Prev_SMA20']) & (nifty[close_col] < nifty['SMA20'])

# Simulate trading 1 share and record trades
position = 0
buy_price = 0
profit = 0
trades = []

for idx, row in nifty.iterrows():
    if position == 0 and row['Buy_Signal']:
        position = 1
        buy_price = row[close_col]
        trades.append({'Date': idx.date(), 'Action': 'Buy', 'Price': buy_price, 'Profit': None})
    elif position == 1 and row['Sell_Signal']:
        position = 0
        sell_price = row[close_col]
        trade_profit = sell_price - buy_price
        profit += trade_profit
        trades.append({'Date': idx.date(), 'Action': 'Sell', 'Price': sell_price, 'Profit': trade_profit})

# If still holding position at the end, sell at last close
if position == 1:
    last_close = nifty.iloc[-1][close_col]
    trade_profit = last_close - buy_price
    profit += trade_profit
    trades.append({'Date': nifty.index[-1].date(), 'Action': 'Sell', 'Price': last_close, 'Profit': trade_profit})

# Print trades and total profit/loss
for t in trades:
    if t['Action'] == 'Buy':
        print(f"Buy at {t['Price']} on {t['Date']}")
    else:
        print(f"Sell at {t['Price']} on {t['Date']} | P&L: {t['Profit']:.2f}")
print(f"\nTotal Profit/Loss: {profit:.2f}")

# Save main data to CSV
nifty.to_csv('nifty_sma_crossover_backtest.csv')

# Save trade log to CSV
trades_df = pd.DataFrame(trades)
trades_df.to_csv('nifty_sma_trades.csv', index=False)

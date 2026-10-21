import yfinance as yf
import pandas as pd
import os

# NIFTY 50 ticker on Yahoo Finance
ticker_symbol = "^NSEI"
ticker = yf.Ticker(ticker_symbol)

print(f"Downloading historical 5-minute data for {ticker_symbol}...")

# yfinance restricts 5-minute intraday data to a maximum of 60 days.
# For multi-year data, the AI will later need to train on 1-hour or 1-day intervals.
nifty_data = ticker.history(period="60d", interval="5m")

if not nifty_data.empty:
    # Clean the dataset by removing irrelevant corporate action columns
    nifty_data = nifty_data.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')
    
    # Create a dedicated directory for machine learning datasets
    os.makedirs("data", exist_ok=True)
    
    file_path = "data/nifty_5m_historical.csv"
    
    # Export the structured DataFrame to a CSV file
    nifty_data.to_csv(file_path)
    
    print(f"Successfully saved {len(nifty_data)} rows of NIFTY data to {file_path}")
    print("\nSample Data:")
    print(nifty_data.head())
else:
    print("Failed to download data. Check the ticker symbol or network connection.")
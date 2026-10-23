import yfinance as yf
import pandas as pd

print("Downloading last 6 months of NIFTY 50 data...")

# The ticker symbol for NIFTY 50 on Yahoo Finance is ^NSEI
nifty50_data = yf.download("^NSEI", period="6mo", progress=False)

# Save it to a CSV file matching the name in our backtester
csv_filename = "nifty50_test_data.csv"
nifty50_data.to_csv(csv_filename)

print(f"Success! Data saved to {csv_filename}")
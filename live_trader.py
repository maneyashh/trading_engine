import os
import time
import numpy as np
import pandas as pd
import yfinance as yf
from sb3_contrib import RecurrentPPO
from huggingface_hub import hf_hub_download
from algo_bot.learning.trading_env import NiftyTradingEnv

def fetch_live_market_data():
    """Fetches the latest 5-minute candles for NIFTY 50"""
    data = yf.download("^NSEI", period="5d", interval="5m", progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    data = data.reset_index()
    data.columns = [str(col).lower() for col in data.columns]
    data.to_csv("data/live_market_feed.csv", index=False)
    return "data/live_market_feed.csv"

print("\n--- Booting NIFTY 50 Autonomous Live Trader ---")

# 1. Fetch the reigning Champion from the Cloud Vault
print("Syncing with Hugging Face for the latest Champion...")
try:
    champion_path = hf_hub_download(
        repo_id="maneyashh/nifty-trading-brain",
        filename="champion_latest.zip",
        token=os.environ.get("HF_TOKEN")
    )
except Exception as e:
    print("Cloud sync failed. Falling back to local champion_v1...")
    champion_path = "models/champion_v1.zip"

# 2. Initialize the Live Environment
live_data_path = fetch_live_market_data()
env = NiftyTradingEnv(data_path=live_data_path)
env.current_fee = 40.0 # Real-world friction on

print("Loading LSTM Neural Pathways...")
model = RecurrentPPO.load(champion_path, env=env)

# 3. The Live Paper Trading Loop
lstm_states = None
episode_starts = np.ones((1,), dtype=bool)

print("\nSystem Armed. Awaiting market pulses...\n")
while True:
    try:
        # Update market data
        live_data_path = fetch_live_market_data()
        env.df = pd.read_csv(live_data_path)
        
        # Get the latest observation (simulating the current live candle)
        env.current_step = len(env.df) - 2 
        obs = env._get_observation()
        
        # LSTM Brain decides the next move
        action, lstm_states = model.predict(
            obs,
            state=lstm_states,
            episode_start=episode_starts,
            deterministic=True
        )
        
        action_val = action.item() if isinstance(action, np.ndarray) else action
        action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
        
        current_price = env.prices[env.current_step]
        print(f"[{time.strftime('%H:%M:%S')}] NIFTY 50: {current_price:.2f} | AI DECISION: {action_map[action_val]}")
        
        episode_starts = np.zeros((1,), dtype=bool) # Memory continuity
        
        # Sleep for 5 minutes before checking the next candle
        time.sleep(300)
        
    except KeyboardInterrupt:
        print("\nLive trading manually terminated.")
        break
    except Exception as e:
        print(f"Market stream interrupted: {e}. Retrying in 60 seconds...")
        time.sleep(60)
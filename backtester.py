import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from huggingface_hub import hf_hub_download
from sb3_contrib import RecurrentPPO # Changed to support your LSTM Brain
from algo_bot.learning.trading_env import NiftyTradingEnv # Exact import from your repo

# 1. Download the Champion Model
print("Pulling LSTM champion weights from Hugging Face...")
model_path = hf_hub_download(
    repo_id="maneyashh/nifty-trading-brain",
    filename="champion_v2.zip", 
    token=os.environ.get("HF_TOKEN")
)

# 2. Load the LSTM Brain
print("Loading Recurrent Neural Network...")
model = RecurrentPPO.load(model_path)

# 3. Initialize your Custom Trading Environment
print("Setting up NiftyTradingEnv...")
# Using data_path= to match your env's __init__ requirements
env = NiftyTradingEnv(data_path="nifty50_test_data.csv")
env.current_fee = 0.0 # Running the backtest frictionless first

# 4. Run the Backtest Simulation
obs, _ = env.reset()
done = False
portfolio_values = []

# LSTM Memory State Tracking variables
lstm_states = None
episode_starts = np.ones((1,), dtype=bool)

print("Initiating historical backtest...")
while not done:
    # LSTM requires us to pass the memory states back and forth
    action, lstm_states = model.predict(
        obs,
        state=lstm_states,
        episode_start=episode_starts,
        deterministic=True
    )
    
    obs, reward, done, truncated, info = env.step(action)
    episode_starts = done # Update episode start state
    
    # Track portfolio value for plotting
    # Adjust 'portfolio_value' if your env uses a different dictionary key like 'net_worth'
    portfolio_values.append(info.get('portfolio_value', 100000))
    
    if done or truncated:
        break

# 5. Visualize Performance
plt.figure(figsize=(12, 6))
plt.plot(portfolio_values, label="AI Portfolio Value", color="#00ff00")
plt.title("NIFTY 50 LSTM Trading Engine - Out of Sample Backtest")
plt.xlabel("Trading Steps")
plt.ylabel("Portfolio Value (INR)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.style.use('dark_background') # Matches THE 5000 DAY BLUEPRINT aesthetic

plt.savefig("backtest_results.png")
print("Backtest complete. Results saved as 'backtest_results.png'.")
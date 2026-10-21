import os
from stable_baselines3 import PPO
from trading_env import NiftyTradingEnv

os.makedirs("models", exist_ok=True)
env = NiftyTradingEnv(data_path="data/nifty_5m_historical.csv")

print("Loading the Phase 1 Brain (Zero-Fee Experience)...")
# Load the existing brain and attach it to the new fee-enabled environment
model = PPO.load("models/nifty_ppo_model", env=env)

print("Phase 2: Hardening the AI against ₹40 Brokerage Fees...")
# Train the existing brain for another 500,000 steps to adapt
model.learn(total_timesteps=500_000)

model.save("models/nifty_ppo_model")
print("Phase 2 Curriculum complete. Hardened model saved.")
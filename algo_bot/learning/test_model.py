from stable_baselines3 import PPO
from trading_env import NiftyTradingEnv

# 1. Initialize the Trading Environment
env = NiftyTradingEnv(data_path="data/nifty_5m_historical.csv")

# 2. Load the trained AI brain
print("Loading the trained AI brain...")
model = PPO.load("models/nifty_ppo_model")

# 3. Reset the environment to the beginning of the dataset
obs, _ = env.reset()
done = False

print(f"Starting Balance: ₹{env.balance}")
print("Running market simulation...")

# 4. Loop through the historical data tick-by-tick
while not done:
    # The AI predicts the best action based on the current observation
    action, _states = model.predict(obs)
    
    # The environment executes the action and returns the new state
    obs, reward, done, truncated, info = env.step(action)

print("\n--- Simulation Complete ---")
print(f"Final Balance: ₹{env.balance:.2f}")
profit = env.balance - 2700.0
print(f"Total Profit/Loss: ₹{profit:.2f}")
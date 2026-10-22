import os
import sys
from sb3_contrib import RecurrentPPO
from huggingface_hub import HfApi

# Link to your custom environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from algo_bot.learning.trading_env import NiftyTradingEnv

# Cloud Configuration
HF_REPO = "maneyashh/nifty-trading-brain"  # CHANGE THIS TO YOUR HF USERNAME
api = HfApi()

# 1. Initialize the Environment
import glob

# Auto-detect the massive CSV file mounted by Kaggle
dataset_folder = "/kaggle/input/nse-nifty-50-index-minute-data-2015-to-2025"
csv_files = glob.glob(f"{dataset_folder}/*.csv")

if csv_files:
    active_data = csv_files[0]
    print(f"Deep History Found: Loading {active_data}...")
else:
    # Fallback if testing locally on your Codespace
    active_data = "data/nifty_5m_historical.csv"
    print("Warning: Using local short-term dataset.")

env = NiftyTradingEnv(data_path=active_data)
env.current_fee = 0.0  # Start with zero friction

# 2. Build the LSTM Brain (Working Memory)
policy_kwargs = dict(
    lstm_hidden_size=256,
    n_lstm_layers=2,
    net_arch=dict(pi=[128, 128], vf=[128, 128])
)

print("Forging the LSTM Recurrent Brain...")
model = RecurrentPPO(
    "MlpLstmPolicy", 
    env, 
    verbose=1, 
    ent_coef=0.05, 
    batch_size=256,
    policy_kwargs=policy_kwargs
)

os.makedirs("models", exist_ok=True)

# 3. The Evolutionary Loop (Generations)
generations = 5
timesteps_per_gen = 50_000

for gen in range(1, generations + 1):
    print(f"\n--- Generation {gen} | Current Fee Friction: ₹{env.current_fee} ---")
    
    # Train the brain
    model.learn(total_timesteps=timesteps_per_gen)
    
    # Save the Champion locally
    model_path = f"models/champion_v{gen}.zip"
    model.save(model_path)
    print(f"Generation {gen} Champion saved locally.")
    
    # Push to Hugging Face Cloud Vault
    try:
        api.upload_file(
            path_or_fileobj=model_path,
            path_in_repo=f"champion_v{gen}.zip",
            repo_id=HF_REPO
        )
        print("SUCCESS: Champion brain pushed to Hugging Face Vault!")
    except Exception as e:
        print(f"WARNING: Cloud upload failed. Is your HF_REPO string correct? Error: {e}")

    # Dynamic Fee Annealing: Crank up the difficulty for the next generation
    if env.current_fee < 40.0:
        env.current_fee += 5.0
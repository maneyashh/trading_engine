import os

print("--- Kaggle Supercomputer Initializing ---")

# 1. Download your latest code from GitHub
os.system("git clone https://github.com/maneyashh/trading_engine.git")
os.chdir("trading_engine")

# 2. Inject the Hugging Face Token from Kaggle's secret environment
HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.system(f"huggingface-cli login --token {HF_TOKEN}")

# 3. Install the required AI libraries
os.system("pip install huggingface_hub sb3-contrib")

# 4. Start the 12-Hour Evolutionary Loop
print("--- Launching the Apex Supervisor ---")
os.system("python apex_supervisor.py")
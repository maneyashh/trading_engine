import os

print("--- Kaggle Supercomputer Initializing ---")

# 1. Download your latest code from GitHub
os.system("git clone https://github.com/maneyashh/trading_engine.git")
os.chdir("trading_engine")

# 2. Inject Secrets from Kaggle's environment
HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.system(f"huggingface-cli login --token {HF_TOKEN}")

# Expose NewsAPI and Gemini keys to the environment variables
os.environ["NEWS_API_KEY"] = os.environ.get("NEWS_API_KEY", "")
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

# 3. Install the required AI libraries
os.system("pip install huggingface_hub sb3-contrib newsapi-python google-generativeai")

# 4. Start the 12-Hour Evolutionary Loop
print("--- Launching the Apex Supervisor ---")
os.system("python apex_supervisor.py")
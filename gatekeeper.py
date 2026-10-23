import os
import numpy as np
from sb3_contrib import RecurrentPPO
from algo_bot.learning.trading_env import NiftyTradingEnv

def evaluate_model(model_path, data_path="data/nifty_5m_historical.csv"):
    print(f"\n--- Gatekeeper Arena Evaluation: {model_path} ---")
    
    # Initialize environment with maximum real-world friction
    env = NiftyTradingEnv(data_path=data_path)
    env.current_fee = 40.0 
    
    if not os.path.exists(model_path):
        print(f"Model {model_path} not found. Skip evaluation.")
        return -np.inf

    try:
        model = RecurrentPPO.load(model_path, env=env)
    except Exception as e:
        print(f"Gatekeeper failed to load model: {e}")
        return -np.inf
        
    obs, _ = env.reset()
    done = False
    
    # LSTM state tracking
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    
    portfolio_values = []
    winning_trades = 0
    total_trades = 0
    previous_position = 0
    entry_worth = env.balance
    
    while not done:
        action, lstm_states = model.predict(
            obs,
            state=lstm_states,
            episode_start=episode_starts,
            deterministic=True
        )
        
        # sb3 predict returns an array; extract the scalar action
        action_val = action.item() if isinstance(action, np.ndarray) else action
        
        obs, reward, done, truncated, info = env.step(action_val)
        episode_starts = done
        
        current_worth = info.get('net_worth', env.balance)
        portfolio_values.append(current_worth)
        
        # Track Win Rate: Check if net worth increased after a Sell (Action 2)
        if action_val == 2 and previous_position == 1:
            total_trades += 1
            if current_worth > entry_worth:
                winning_trades += 1
                
        # Mark net worth at the time of a Buy (Action 1)
        if action_val == 1 and previous_position == 0:
            entry_worth = current_worth
            
        previous_position = env.position
        
        if done or truncated:
            break
            
    # Calculate Core Metrics
    initial_balance = 2700.0
    final_balance = portfolio_values[-1]
    total_profit = final_balance - initial_balance
    return_pct = (total_profit / initial_balance) * 100
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    # Calculate Maximum Drawdown
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (peak - portfolio_values) / peak
    max_drawdown = np.max(drawdown) * 100
    
    print(f"Total Trades Taken : {total_trades}")
    print(f"Win Rate           : {win_rate:.2f}%")
    print(f"Max Drawdown       : {max_drawdown:.2f}%")
    print(f"Total Return       : ₹{total_profit:.2f} ({return_pct:.2f}%)")
    
    return return_pct

if __name__ == "__main__":
    # Test the local champion (ensure you have a models/champion_v1.zip or adjust the name)
    score = evaluate_model("models/champion_v1.zip")
    
    if score > 0:
        print("\nGATEKEEPER VERDICT: PASS (Promoted)")
    else:
        print("\nGATEKEEPER VERDICT: FAIL (Rejected)")
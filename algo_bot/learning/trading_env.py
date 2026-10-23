import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import numpy as np

class NiftyTradingEnv(gym.Env):
    """A custom reinforcement learning trading environment for NIFTY 50"""
    
    def __init__(self, data_path="data/nifty_5m_historical.csv"):
        super(NiftyTradingEnv, self).__init__()
        
        self.df = pd.read_csv(data_path)
        
        # FEATURE ENGINEERING: Moving Averages
        self.df['SMA_5'] = self.df['Close'].rolling(window=5).mean()
        self.df['SMA_20'] = self.df['Close'].rolling(window=20).mean()
        
        # FEATURE ENGINEERING: 14-Period RSI
        delta = self.df['Close'].diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = -1 * delta.clip(upper=0).rolling(window=14).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        
        # FEATURE ENGINEERING: MACD (12-EMA minus 26-EMA)
        ema_12 = self.df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = self.df['Close'].ewm(span=26, adjust=False).mean()
        self.df['MACD'] = ema_12 - ema_26
        self.df['Signal_Line'] = self.df['MACD'].ewm(span=9, adjust=False).mean()
        
        # FEATURE ENGINEERING: Bollinger Bands (20-SMA +/- 2 Standard Deviations)
        std_20 = self.df['Close'].rolling(window=20).std()
        self.df['Upper_BB'] = self.df['SMA_20'] + (std_20 * 2)
        self.df['Lower_BB'] = self.df['SMA_20'] - (std_20 * 2)
        
        # Backfill missing data from rolling windows
        self.df = self.df.bfill()
        
        # Extract numpy arrays for ultra-fast access during training
        self.prices = self.df['Close'].values
        self.volume = self.df['Volume'].values
        self.sma_5 = self.df['SMA_5'].values
        self.sma_20 = self.df['SMA_20'].values
        self.rsi = self.df['RSI'].values
        self.macd = self.df['MACD'].values
        self.signal_line = self.df['Signal_Line'].values
        self.upper_bb = self.df['Upper_BB'].values
        self.lower_bb = self.df['Lower_BB'].values
        
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)
        
        self.current_step = 0
        self.balance = 2700.0  
        self.position = 0 
        self.entry_price = 0.0
        self.current_fee = 40.0 # Supervisor controls friction

    def reset(self, seed=None):
        self.current_step = 0
        self.balance = 2700.0
        self.position = 0
        return self._get_observation(), {}

    def _get_observation(self):
        # NORMALIZATION: Scale all 10 values down to a range close to [-1, 1]
        norm_price = self.prices[self.current_step] / 30000.0
        norm_balance = self.balance / 10000.0
        norm_sma5 = self.sma_5[self.current_step] / 30000.0
        norm_sma20 = self.sma_20[self.current_step] / 30000.0
        norm_rsi = self.rsi[self.current_step] / 100.0
        
        norm_vol = self.volume[self.current_step] / 1000000.0
        norm_macd = self.macd[self.current_step] / 100.0
        norm_signal = self.signal_line[self.current_step] / 100.0
        norm_upper_bb = self.upper_bb[self.current_step] / 30000.0
        norm_lower_bb = self.lower_bb[self.current_step] / 30000.0

        return np.array([
            norm_price, 
            norm_balance,
            norm_sma5,
            norm_sma20,
            norm_rsi,
            norm_vol,
            norm_macd,
            norm_signal,
            norm_upper_bb,
            norm_lower_bb
        ], dtype=np.float32)

    def step(self, action):
        current_price = self.prices[self.current_step]
        
        # 1. Calculate net worth BEFORE the action
        unrealized_pnl = (current_price - self.entry_price) if self.position == 1 else 0
        prev_net_worth = self.balance + unrealized_pnl
        
        # 2. Execute the chosen action
        if action == 1 and self.position == 0:
            self.position = 1
            self.entry_price = current_price
            
        elif action == 2 and self.position == 1:
            gross_profit = current_price - self.entry_price
            net_profit = gross_profit - self.current_fee  # FIX: Uses dynamic fee
            self.balance += net_profit
            self.position = 0
            self.entry_price = 0.0
            
        # 3. Move time forward by one 5-minute candle
        self.current_step += 1
        done = self.current_step >= len(self.prices) - 1
        
        # 4. Calculate net worth AFTER the action and price movement
        new_price = self.prices[self.current_step]
        new_unrealized_pnl = (new_price - self.entry_price) if self.position == 1 else 0
        new_net_worth = self.balance + new_unrealized_pnl
        
        # 5. The reward is strictly the change in net worth.
        reward = (new_net_worth - prev_net_worth) / 10.0
        
        return self._get_observation(), reward, done, False, {'net_worth': new_net_worth}

if __name__ == "__main__":
    env = NiftyTradingEnv(data_path="data/nifty_5m_historical.csv")
    obs, _ = env.reset()
    print(f"Environment Initialized. AI Vision: {obs}")
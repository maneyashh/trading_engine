import gymnasium as gym
import numpy as np
from gymnasium import spaces

class TradingEnv(gym.Env):
    def __init__(self, df):
        super(TradingEnv, self).__init__()
        self.df = df
        self.current_step = 0
        
        # Example: 3 actions (0=Hold, 1=Buy, 2=Sell)
        self.action_space = spaces.Discrete(3)
        
        # NOTE: Change shape=(5,) to match the exact number of features your AI expects!
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.portfolio_value = 100000.0  # Starting with ₹1,00,000
        # Returning dummy data to match the shape
        return np.zeros(self.observation_space.shape, dtype=np.float32), {}

    def step(self, action):
        self.current_step += 1
        
        done = self.current_step >= len(self.df) - 1
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        reward = 0.0
        
        # Track simulated portfolio value
        info = {'portfolio_value': self.portfolio_value}
        
        return obs, reward, done, False, info
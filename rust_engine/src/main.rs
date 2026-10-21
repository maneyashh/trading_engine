use pyo3::prelude::*;
use pyo3::types::PyList;

fn main() -> PyResult<()> {
    println!("Initializing Rust Execution Engine...");

    // Open a completely safe bridge into the Python environment
    Python::with_gil(|py| {
        // 1. Import Python's sys module to add your algo_bot directory to the path
        let sys = py.import("sys")?;
        let path: &PyList = sys.getattr("path")?.downcast()?;
        path.insert(0, "../algo_bot/learning")?;

        println!("Connecting to the Python Brain...");

        // 2. Write inline Python to load the model
        let python_code = r#"
from stable_baselines3 import PPO
import numpy as np

def get_trade_decision(price, balance, sma5, sma20, rsi):
    # Load the trained model (adjust path as needed from where Rust runs)
    model = PPO.load("/workspaces/trading_engine/models/nifty_ppo_model")
    
    # Normalize the incoming live data exactly like the training environment
    obs = np.array([
        price / 30000.0, 
        balance / 10000.0, 
        sma5 / 30000.0, 
        sma20 / 30000.0, 
        rsi / 100.0
    ], dtype=np.float32)
    
    # Predict the action: 0 (Hold), 1 (Buy), 2 (Sell)
    action, _ = model.predict(obs)
    return int(action)
"#;
        // 3. Compile the Python code inside Rust
        let brain_module = PyModule::from_code(py, python_code, "brain.py", "brain")?;
        
        // 4. Feed live market data to the model
        // Example: NIFTY at 24000, 2700 balance, SMA5 at 23990, SMA20 at 23950, RSI at 65
        let action: i32 = brain_module
            .getattr("get_trade_decision")?
            .call1((24000.0, 2700.0, 23990.0, 23950.0, 65.0))?
            .extract()?;

        match action {
            0 => println!("Rust Engine Decision: HOLD. Waiting for setup."),
            1 => println!("Rust Engine Decision: BUY! Sending market order..."),
            2 => println!("Rust Engine Decision: SELL! Closing position..."),
            _ => println!("Unknown action received."),
        }

        Ok(())
    })
}
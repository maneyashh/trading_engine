use totp_rs::{Algorithm, Secret, TOTP};
use reqwest::Client;
use serde_json::json;
use std::time::{SystemTime, UNIX_EPOCH, Duration};

// 1. Define states to track what the bot currently owns
#[derive(PartialEq, Debug)]
enum Position {
    None,
    LongCall,
    LongPut,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 2. Groww Credentials
    let api_key = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1ODA5NDQ1NzYsImlhdCI6MTc5MjU0NDU3NiwibmJmIjoxNzkyNTQ0NTc2LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCIwZDJiYzM2Yy03ZWI3LTQ5YWQtODM2NS1mM2ZhNzhhODEzOTZcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiODk1ZjM1NTctNTZmNi00NWVkLTljN2MtYTc1MzViYWVlZDM3XCIsXCJkZXZpY2VJZFwiOlwiMzFhOTZkNDItYmM5Yi01OGNmLTgzMjYtNjQ0YzIwNzZmNGU4XCIsXCJzZXNzaW9uSWRcIjpcImVlNDQ4YzVmLWRkYmMtNDNkMi1hNTZjLThlNWRjYzgwYmM4Y1wiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkdZQUhoUmV0dVBYK2xsWnN6OEVMa1ZSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIyNDAxOjQ5MDA6NTYwZTo3ODZiOmM5MTk6MzRkNzpmZDA4OjdmZDMsMTcyLjY5Ljg2LjE4NiwzNS4yNDEuMjMuMTIzXCIsXCJ0d29GYUV4cGlyeVRzXCI6MjU4MDk0NDU3NjY0NCxcInZlbmRvck5hbWVcIjpcImdyb3d3QXBpXCJ9IiwiaXNzIjoiYXBleC1hdXRoLXByb2QtYXBwIn0.OH39lFuG6-Z09RO7HPYxHd4w3oFchSjYWWgqdYVCUJ2Xzgua6PZZC1GF5yg-vCig8KD2t_3Dn6X3txCGRc851g"; 
    let totp_secret_str = "RUAMTTAD6U4YPGO3F4LSN3TO3LNIMZBS"; 

    // Generate TOTP
    let clean_secret = totp_secret_str.replace(" ", "").to_uppercase();
    let secret = Secret::Encoded(clean_secret);
    let totp = TOTP::new(
        Algorithm::SHA1,
        6,
        1,
        30,
        secret.to_bytes().expect("Failed to parse the TOTP Secret."),
    ).unwrap();
    let current_code = totp.generate_current().unwrap();
    println!("1. TOTP Generated: {}", current_code);

    // Authenticate with Groww
    let client = Client::new();
    let auth_res = client.post("https://api.groww.in/v1/token/api/access")
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&json!({
            "key_type": "totp",
            "totp": current_code
        }))
        .send()
        .await?;

    let auth_json: serde_json::Value = auth_res.json().await?;
    let access_token = match auth_json.get("token").and_then(|t| t.as_str()) {
        Some(token) => token,
        None => {
            eprintln!("Authentication failed: {:?}", auth_json);
            return Ok(());
        }
    };
    println!("2. Session Authenticated Successfully.\n");

    // Initialize position tracker
    let mut current_position = Position::None;
    let order_url = "https://api.groww.in/v1/order/create";

    // === THE INFINITE TRADING LOOP ===
    loop {
        println!("[{:?}] Fetching live NIFTY 50 data...", SystemTime::now());
        let yf_url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=5m&range=1d";
        
        match client.get(yf_url).header("User-Agent", "Mozilla/5.0").send().await {
            Ok(yf_res) => {
                if yf_res.status().is_success() {
                    let yf_json: serde_json::Value = yf_res.json().await.unwrap_or_default();
                    
                    if let Some(result) = yf_json["chart"]["result"].as_array().and_then(|r| r.first()) {
                        if let Some(quotes) = result["indicators"]["quote"].as_array().and_then(|q| q.first()) {
                            if let Some(close_prices) = quotes["close"].as_array() {
                                
                                let valid_prices: Vec<f64> = close_prices.iter()
                                    .filter_map(|p| p.as_f64())
                                    .collect();

                                if valid_prices.len() >= 5 {
                                    let latest_price = valid_prices.last().unwrap();
                                    let sum: f64 = valid_prices.iter().rev().take(5).sum();
                                    let sma_5 = sum / 5.0;
                                    
                                    println!("Live NIFTY: {:.2} | 5-SMA: {:.2}", latest_price, sma_5);
                                    println!("--- TRADING SIGNAL ---");

                                    // BULLISH CROSSOVER
                                    if *latest_price > sma_5 {
                                        println!("Trend: BULLISH 🟢");
                                        if current_position != Position::LongCall {
                                            println!("Action: Crossing above SMA! Executing BUY order for CE...");
                                            
                                            let millis = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();
                                            let order_ref_id = format!("ORD{:011}", millis % 100_000_000_000);
                                            
                                            // TOMORROW: Change "YESBANK-EQ" to your actual NIFTY CE symbol, "CASH" to "FNO", and quantity to 25
                                            let order_payload = json!({
                                                "order_reference_id": order_ref_id,
                                                "trading_symbol": "YESBANK-EQ", 
                                                "segment": "CASH", 
                                                "exchange": "NSE",
                                                "transaction_type": "BUY",
                                                "order_type": "LIMIT",
                                                "price": 1.00, 
                                                "product": "CNC",
                                                "validity": "DAY",
                                                "quantity": 1 
                                            });

                                            let order_res = client.post(order_url)
                                                .header("Authorization", format!("Bearer {}", access_token))
                                                .header("Content-Type", "application/json")
                                                .header("Accept", "application/json")
                                                .header("X-API-VERSION", "1.0")
                                                .json(&order_payload)
                                                .send()
                                                .await;

                                            match order_res {
                                                Ok(res) => println!("Order API Status: {} | Response: {:?}", res.status(), res.text().await.unwrap_or_default()),
                                                Err(e) => println!("Failed to send order: {}", e),
                                            }
                                            
                                            current_position = Position::LongCall;
                                        } else {
                                            println!("Action: Already holding Call option. Holding position.");
                                        }
                                    } 
                                    // BEARISH CROSSOVER
                                    else {
                                        println!("Trend: BEARISH 🔴");
                                        if current_position != Position::LongPut {
                                            println!("Action: Crossing below SMA! Executing BUY order for PE...");
                                            
                                            let millis = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();
                                            let order_ref_id = format!("ORD{:011}", millis % 100_000_000_000);
                                            
                                            // TOMORROW: Change "YESBANK-EQ" to your actual NIFTY PE symbol, "CASH" to "FNO", and quantity to 25
                                            let order_payload = json!({
                                                "order_reference_id": order_ref_id,
                                                "trading_symbol": "YESBANK-EQ", 
                                                "segment": "CASH",
                                                "exchange": "NSE",
                                                "transaction_type": "BUY",
                                                "order_type": "LIMIT",
                                                "price": 1.00, 
                                                "product": "CNC",
                                                "validity": "DAY",
                                                "quantity": 1 
                                            });

                                            let order_res = client.post(order_url)
                                                .header("Authorization", format!("Bearer {}", access_token))
                                                .header("Content-Type", "application/json")
                                                .header("Accept", "application/json")
                                                .header("X-API-VERSION", "1.0")
                                                .json(&order_payload)
                                                .send()
                                                .await;

                                            match order_res {
                                                Ok(res) => println!("Order API Status: {} | Response: {:?}", res.status(), res.text().await.unwrap_or_default()),
                                                Err(e) => println!("Failed to send order: {}", e),
                                            }
                                            
                                            current_position = Position::LongPut;
                                        } else {
                                            println!("Action: Already holding Put option. Holding position.");
                                        }
                                    }
                                    println!("----------------------\n");
                                }
                            }
                        }
                    }
                } else {
                    println!("Yahoo Finance returned an error status: {}", yf_res.status());
                }
            },
            Err(e) => println!("Network error fetching market data: {}", e),
        }

        tokio::time::sleep(Duration::from_secs(10)).await;
    }
}
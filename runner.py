import os
import pandas as pd
from datetime import datetime
from core.data_fetcher import fetch_crypto_data
from core.discord_notifier import send_discord_message
from models import logistic_model, random_forest

# === CONFIG ===
webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'  # Your real webhook
log_file = "prediction_logs.csv"

# === STEP 1: Get Data ===
data = fetch_crypto_data(symbol='BTC/USDT', timeframe='1h', limit=500)

# === STEP 2: Models ===
models = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest,
}

# === STEP 3: Run Models ===
for name, module in models.items():
    try:
        signal, prob, df = module.run_model(data.copy())

        # Calculate true next result
        try:
            next_return = df['close'].pct_change().shift(-1).iloc[-1]
            actual_up = int(next_return > 0)
        except:
            next_return = None
            actual_up = None

        # Log row
        log_row = pd.DataFrame([{
            'timestamp': datetime.utcnow(),
            'model': name,
            'signal': signal,
            'prob': round(prob, 4),
            'actual_up': actual_up,
            'next_return': next_return
        }])
        log_row.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False)

        # Discord message
        emoji = "🟢 BUY" if signal == 1 else "🔴 NO BUY"
        msg = f"**{name}**\nProb: `{prob:.2f}` → Signal: `{signal}` {emoji}"
        send_discord_message(webhook_url, msg)
        print(f"{name}: Signal {signal}, Prob {prob:.2f}")

    except Exception as e:
        send_discord_message(webhook_url, f"❌ Error in {name}: {str(e)}")
        print(f"Error in {name}: {e}")

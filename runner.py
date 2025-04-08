import os
from core.data_fetcher import fetch_crypto_data
from core.discord_notifier import send_discord_message
from models import logistic_model, random_forest

# ENV: put your Discord webhook here or load from .env later
webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'

# 1. Fetch live data
data = fetch_crypto_data(symbol='BTC/USDT', timeframe='1h', limit=500)

# 2. Run models and send signals
models = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest,
}

for name, module in models.items():
    try:
        signal, prob = module.run_model(data.copy())  # prevent mutation
        emoji = "🟢 BUY" if signal == 1 else "🔴 NO BUY"
        msg = f"**{name}**\nProb: `{prob:.2f}` → Signal: `{signal}` {emoji}"
        send_discord_message(webhook_url, msg)
        print(f"{name}: Signal {signal}, Prob {prob:.2f}")
    except Exception as e:
        send_discord_message(webhook_url, f"❌ Error in {name}: {str(e)}")
        print(f"Error in {name}: {e}")

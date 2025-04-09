import os
import pandas as pd
from datetime import datetime
from core.data_fetcher import fetch_crypto_data
from core.discord_notifier import send_discord_message
from models import logistic_model, random_forest
from core.wallet_tracker import Wallet

wallet = Wallet(starting_cash=1000)


# === CONFIG ===
webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'  # Your real webhook
log_file = "logs/prediction_logs.csv"

wallet_file = 'logs/live_wallet.csv'
initial_cash = 1000
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

    price = data['close'].iloc[-1]
    timestamp = datetime.utcnow()

    if signal == 1 and wallet.crypto == 0.0:
        wallet.buy(price, timestamp, name, prob)
    elif signal == 0 and wallet.crypto > 0.0:
        wallet.sell(price, timestamp, name, prob)

    msg = f"""
    💼 Wallet Value: ${wallet.value(price):.2f}
    💰 Cash: ${wallet.cash:.2f}
    🪙 Crypto: {wallet.crypto:.6f}
    """
    send_discord_message(webhook_url, msg)


    except Exception as e:
        send_discord_message(webhook_url, f"❌ Error in {name}: {str(e)}")
        print(f"Error in {name}: {e}")

# Get current price return
df = data.copy()
df['Return'] = df['close'].pct_change()
df.dropna(inplace=True)

# Simulate this hour’s return
this_return = df['Return'].iloc[-1] if signal == 1 else 0
timestamp = datetime.utcnow()

# Load last balance
if os.path.exists(wallet_file):
    wallet = pd.read_csv(wallet_file)
    last_balance = wallet['balance'].iloc[-1]
else:
    last_balance = initial_cash

# Update balance
new_balance = last_balance * (1 + this_return)

# Save to file
new_row = pd.DataFrame([{
    'timestamp': timestamp,
    'model': name,
    'signal': signal,
    'probability': round(prob, 4),
    'return': round(this_return, 5),
    'balance': round(new_balance, 2)
}])
new_row.to_csv(wallet_file, mode='a', header=not os.path.exists(wallet_file), index=False)

# Discord update
msg = f"""
💸 **Live Wallet Update: {name}**
- Signal: {signal}
- Return: {this_return:.5f}
- New Balance: ${new_balance:.2f}
"""
send_discord_message(webhook_url, msg)

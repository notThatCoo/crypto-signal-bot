import os
import pandas as pd
from datetime import datetime
from core.data_fetcher import fetch_crypto_data
from core.discord_notifier import send_discord_message
from models import logistic_model, random_forest
from core.wallet_tracker import Wallet
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import sqlite3

# === INITIALIZE WALLET ===
wallet = Wallet(starting_cash=1000)

# === CONFIG ===
webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'
db_file = "logs/trades.db"
log_file = "logs/prediction_logs.csv"
wallet_log_file = "logs/wallet_history.csv"


# === SETUP DATABASE ONCE ===
conn = sqlite3.connect(db_file)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS predictions (
    timestamp TEXT,
    model TEXT,
    signal INTEGER,
    prob REAL,
    actual_up INTEGER,
    next_return REAL
)''')
conn.commit()
conn.close()

# === STEP 1: FETCH DATA ===
data = fetch_crypto_data(symbol='BTC/USDT', timeframe='1h', limit=500)

# === STEP 2: DEFINE MODELS ===
models = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest,
}

# === STEP 3: RUN MODELS + TRADE LOGIC ===
for name, module in models.items():
    try:
        signal, prob, df, preds = module.run_model(data.copy())


        # Calculate next return (for evaluation)
        try:
            next_return = df['close'].pct_change().shift(-1).iloc[-1]
            actual_up = int(next_return > 0)
        except:
            next_return = None
            actual_up = None

        # === Log to CSV ===
        log_row = pd.DataFrame([{
            'timestamp': datetime.utcnow(),
            'model': name,
            'signal': signal,
            'prob': round(prob, 4),
            'actual_up': actual_up,
            'next_return': next_return
        }])
        log_row.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False)

        # === Log to SQLite ===
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('''INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?)''', (
            datetime.utcnow().isoformat(),
            name,
            int(signal),
            float(prob),
            int(actual_up) if actual_up is not None else None,
            float(next_return) if next_return is not None else None
        ))
        conn.commit()
        conn.close()

        # === TRADE LOGIC ===
        price = data['close'].iloc[-1]
        timestamp = datetime.utcnow()
        
        # === Buy Logic ===
        if signal == 1:
            if wallet.short_position > 0.0:
                wallet.cover(price, timestamp, name, prob)
            elif wallet.crypto == 0.0:
                wallet.buy(price, timestamp, name, prob)
        
        # === Sell / Short Logic ===
        elif signal == 0:
            if wallet.crypto > 0.0:
                wallet.sell(price, timestamp, name, prob)
            elif wallet.short_position == 0.0:
                wallet.short(price, timestamp, name, prob)

        # === Wallet Status to Discord ===
        wallet_msg = f"💼 Wallet Status: {name} | 💰 Cash: ${wallet.cash:.2f} | 🪙 Crypto: {wallet.crypto:.6f} | 📊 Value: ${wallet.value(price):.2f}"
        send_discord_message(webhook_url, wallet_msg)

        # === Model Evaluation ===
        df['Actual'] = (df['Return'].shift(-1) > 0).astype(int)
        df['Prediction'] = preds
  # or however your model returns signals


        y_true = df['Actual'].dropna()
        y_pred = df['Prediction'].dropna()

        cm = confusion_matrix(y_true, y_pred)
        report = classification_report(y_true, y_pred, digits=2)
        acc = accuracy_score(y_true, y_pred)

        print(f"\n{name} Confusion Matrix:\n", cm)
        print(f"\n{name} Classification Report:\n", report)

        msg = f"📊 {name} Model Evaluation | Accuracy: {acc:.2f}\n{report}"
        send_discord_message(webhook_url, msg)

        print(f"\n🔎 Model: {name} | Signal: {signal} | Prob: {prob:.2f}")
        print("Last 10 Predictions:", preds[-10:])


    except Exception as e:
        send_discord_message(webhook_url, f"❌ Error in {name}: {str(e)}")
        print(f"Error in {name}: {e}")

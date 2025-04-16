import os
import pandas as pd
from datetime import datetime
from core.data_fetcher import fetch_crypto_data
from core.discord_notifier import send_discord_message
from models import logistic_model, random_forest
from core.wallet_tracker import Wallet
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import sqlite3
import matplotlib.pyplot as plt

# === CONFIG ===
LIVE_MODE = False  # Toggle to True for real Kraken trades
webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'
wallet_log_file = "logs/wallet_history.csv"
db_file = "logs/trades.db"
log_file = "logs/prediction_logs.csv"
webhook_url2 = 'https://discord.com/api/webhooks/1361969632805916722/1NCsde4_Q6zBTubiDmoCeSTJLlgTxZYkVclGcIBxqff8jYa1lBnV-mfr9zYp6iV_f2Iy'

# === SETUP DB TABLE ===
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

# === FETCH DATA ===
data = fetch_crypto_data(symbol='BTC/USDT', timeframe='1h', limit=500)

# === ADD TECHNICAL INDICATORS ===
# Relative Strength Index (RSI)
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

data['RSI'] = compute_rsi(data['close'])

# Moving Average Convergence Divergence (MACD)
ema_12 = data['close'].ewm(span=12, adjust=False).mean()
ema_26 = data['close'].ewm(span=26, adjust=False).mean()
data['MACD'] = ema_12 - ema_26

wallet = Wallet(starting_cash=1000)

# === MODELS ===
models = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest,
}

for name, module in models.items():
    try:
        signal, prob, df, preds = module.run_model(data.copy())

        now = datetime.utcnow()
        price = data['close'].iloc[-1]

        # Evaluate target
        try:
            next_return = df['close'].pct_change().shift(-1).iloc[-1]
            actual_up = int(next_return > 0)
        except:
            next_return = None
            actual_up = None

        # Log predictions to file
        log_row = pd.DataFrame([{
            'timestamp': now,
            'model': name,
            'signal': signal,
            'prob': round(prob, 4),
            'actual_up': actual_up,
            'next_return': next_return
        }])
        log_row.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False)

        # Log wallet to file
        wallet_row = pd.DataFrame([{
            'timestamp': now,
            'model': name,
            'value': round(wallet.value(price), 2),
            'cash': round(wallet.cash, 2),
            'crypto': round(wallet.crypto, 6),
            'short_position': round(wallet.short_position, 6),
            'price': round(price, 2)
        }])
        wallet_row.to_csv(wallet_log_file, mode='a', header=not os.path.exists(wallet_log_file), index=False)

        # Log to SQLite
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('''INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?)''', (
            now.isoformat(), name, signal, prob, actual_up, next_return
        ))
        conn.commit()
        conn.close()

        # Execute trade
        if LIVE_MODE:
            from core.kraken_client import place_market_order
            side = 'buy' if signal == 1 else 'sell'
            order = place_market_order('BTC/USDT', side, 0.0001)
            print("Kraken Order:", order)
        else:
            if signal == 1:
                if wallet.short_position > 0.0:
                    wallet.cover(price, now, name, prob)
                elif wallet.crypto == 0.0:
                    wallet.buy(price, now, name, prob)
            elif signal == 0:
                if wallet.crypto > 0.0:
                    wallet.sell(price, now, name, prob)
                elif wallet.short_position == 0.0:
                    wallet.short(price, now, name, prob)

        # Wallet update
        wallet_msg = f"Wallet Status: {name} | Cash: ${wallet.cash:.2f} | Crypto: {wallet.crypto:.6f} | Value: ${wallet.value(price):.2f}"
        send_discord_message(webhook_url, wallet_msg)

        # Model evaluation
        df['Actual'] = (df['Return'].shift(-1) > 0).astype(int)
        df['Prediction'] = preds
        y_true = df['Actual'].dropna()
        y_pred = df['Prediction'].dropna()

        acc = accuracy_score(y_true, y_pred)
        cm = confusion_matrix(y_true, y_pred)
        report = classification_report(y_true, y_pred, digits=2)

        print(f"\n{name} Confusion Matrix:\n", cm)
        print(f"\n{name} Classification Report:\n", report)

        send_discord_message(webhook_url, f"{name} Accuracy: {acc:.2f}\n{report}")

        # Portfolio chart
        if os.path.exists(wallet_log_file):
            df_wallet = pd.read_csv(wallet_log_file)
            plt.figure(figsize=(10, 6))
            for model_name in df_wallet['model'].unique():
                sub = df_wallet[df_wallet['model'] == model_name]
                plt.plot(pd.to_datetime(sub['timestamp']), sub['value'], label=model_name)

            plt.title("Portfolio Value Over Time")
            plt.xlabel("Timestamp")
            plt.ylabel("Wallet Value ($)")
            plt.grid()
            plt.legend()
            plt.tight_layout()
            plt.savefig("logs/wallet_growth.png")
            with open("logs/wallet_growth.png", "rb") as f:
                send_discord_message(webhook_url2, "Portfolio Growth Chart", file=f)

    except Exception as e:
        send_discord_message(webhook_url, f"Error in {name}: {str(e)}")
        print(f"Error in {name}: {e}")

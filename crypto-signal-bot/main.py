import ccxt
import pandas as pd
from sklearn.linear_model import LogisticRegression
import datetime
import alpaca_trade_api as tradeapi
import matplotlib.pyplot as plt

# --- Connect to Kraken
kraken = ccxt.kraken()

# --- Get Historical Data (BTC/USD)
symbol = 'BTC/USD'
since = kraken.parse8601('2023-01-01T00:00:00Z')  # Start date

ohlcv = kraken.fetch_ohlcv(symbol, timeframe='1h', since=since, limit=1000)

# --- Put into DataFrame
data = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
data['Timestamp'] = pd.to_datetime(data['Timestamp'], unit='ms')
data.set_index('Timestamp', inplace=True)

# --- Feature Engineering
data['SMA_5'] = data['Close'].rolling(window=5).mean()
data['SMA_20'] = data['Close'].rolling(window=20).mean()
data['Return'] = data['Close'].pct_change()
data.dropna(inplace=True)

# --- Logistic Regression
X = data[['SMA_5', 'SMA_20', 'Return']]
y = (data['Return'].shift(-1) > 0).astype(int)[:-1]

model = LogisticRegression()
model.fit(X[:-1], y)

today_features = X.iloc[[-1]]
predicted_prob = model.predict_proba(today_features)[0][1]
predicted_signal = int(predicted_prob > 0.5)

# --- Save Prediction
today_signal = pd.DataFrame({
    'Date': [data.index[-1]],
    'Predicted_Prob': [predicted_prob],
    'Predicted_Signal': [predicted_signal]
})
today_signal.to_csv('today_kraken_signal.csv', index=False)

print("Prediction saved.")
print("Probability of Price Going Up:", predicted_prob)
print("Signal (1=Buy, 0=No Buy):", predicted_signal)


import requests

# --- Discord Webhook URL ---
webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'

# --- Create message ---
message = f"""
🚨 Crypto Signal 🚨
Date: {data.index[-1]}
Probability of Price Going Up: {predicted_prob:.2f}
Signal: {"BUY" if predicted_signal == 1 else "NO BUY"}
"""

# --- Send to Discord ---
payload = {"content": message}
requests.post(webhook_url, json=payload)

print("Signal sent to Discord.")

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# --- More Feature Engineering ---
data['Volatility'] = data['Return'].rolling(10).std()
data['Momentum'] = data['Close'] - data['Close'].shift(10)

# Drop rows with NaN from new features
data.dropna(inplace=True)

# Update X and y
X = data[['SMA_5', 'SMA_20', 'Return', 'Volatility', 'Momentum']]
y = (data['Return'].shift(-1) > 0).astype(int)[:-1]

# Train Random Forest
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X[:-1], y)

# Evaluate Model
y_true = y
y_pred = model.predict(X[:-1])
print(confusion_matrix(y_true, y_pred))
print(classification_report(y_true, y_pred))

# Add Predictions to DataFrame
data = data.iloc[:len(y_pred)]
data['Predicted_Prob'] = model.predict_proba(X[:-1])[:,1]
data['Predicted_Signal'] = (data['Predicted_Prob'] > 0.5).astype(int)

# Backtest
data['Strategy_Return'] = data['Return'] * data['Predicted_Signal']
data['Cumulative_Strategy_Return'] = (1 + data['Strategy_Return']).cumprod()
data['Cumulative_Buy_and_Hold'] = (1 + data['Return']).cumprod()

# Save backtest
data[['Cumulative_Strategy_Return', 'Cumulative_Buy_and_Hold']].to_csv('backtest_results.csv')

# Discord Summary
summary_message = f"""
🧠 Upgraded Bot Report
Final Strategy Return: {data['Cumulative_Strategy_Return'].iloc[-1]:.2f}x
Final Buy & Hold Return: {data['Cumulative_Buy_and_Hold'].iloc[-1]:.2f}x
Model: Random Forest w/ Volatility + Momentum
"""

payload = {"content": summary_message}
requests.post(webhook_url, json=payload)

print("Upgraded model complete. Summary sent to Discord.")


# 🔐 Use your actual API Key and Secret here
ALPACA_API_KEY = 'PKK9QBIA6BQQYR72QCW7'
ALPACA_SECRET_KEY = 'PKK9QBIA6BQQYR72QCW7'
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'  # Use paper trading

# Connect to Alpaca
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

if True:
    try:
        api.submit_order(
            symbol='BTC/USD',
            qty=0.001,  # adjust for your test size
            side='buy',
            type='market',
            time_in_force='gtc'
        )
        print("Trade executed.")
    except Exception as e:
        print("Trade error:", e)
import matplotlib.pyplot as plt

# --- Plotting cumulative returns ---
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['Cumulative_Strategy_Return'], label='Strategy', linewidth=2)
plt.plot(data.index, data['Cumulative_Buy_and_Hold'], label='Buy & Hold', linestyle='--')
plt.title('Cumulative Returns: Strategy vs Buy & Hold')
plt.xlabel('Date')
plt.ylabel('Portfolio Value (x Initial)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('strategy_vs_hold.png')  # Saves image on server
plt.show()
plt.savefig('strategy_vs_hold.png')

with open('strategy_vs_hold.png', 'rb') as f:
    files = {'file': f}
    image_payload = {
        "content": "📊 Cumulative Returns Chart"
    }
    requests.post(webhook_url, data=image_payload, files=files)
from datetime import datetime

# === AUTO-EXECUTION ===
if predicted_signal == 1:
    try:
        # Submit market order
        api.submit_order(
            symbol='BTC/USD',
            qty=0.001,  # Change this to your test size
            side='buy',
            type='market',
            time_in_force='gtc'
        )

        print("Trade executed.")

        # Log to file
        trade_log = pd.DataFrame({
            'Date': [data.index[-1]],
            'Signal': [predicted_signal],
            'Prob': [predicted_prob],
            'Qty': [0.001],
            'Asset': ['BTC/USD']
        })

        trade_log.to_csv('trades.csv', mode='a', header=not os.path.exists('trades.csv'), index=False)

        # Send Discord confirmation
        trade_msg = f"✅ TRADE EXECUTED\nDate: {data.index[-1]}\nAsset: BTC/USD\nQty: 0.001\nProb: {predicted_prob:.2f}"
        requests.post(webhook_url, json={"content": trade_msg})

    except Exception as e:
        print("Trade error:", e)
        requests.post(webhook_url, json={"content": f"❌ TRADE FAILED: {str(e)}"})

import pandas as pd
import matplotlib.pyplot as plt
from core.data_fetcher import fetch_crypto_data
from models import logistic_model, random_forest
from sklearn.metrics import accuracy_score
import numpy as np
from core.discord_notifier import send_discord_message

webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'  # Your real webhook

initial_cash = 1000  # Start with $1,000
df['Simulated_Balance'] = initial_cash * df['Cumulative_Strategy']

final_balance = df['Simulated_Balance'].iloc[-1]
print(f"💰 Simulated final balance: ${final_balance:.2f}")

# === Config ===
model_to_run = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest
}
symbol = 'BTC/USDT'
timeframe = '1h'
limit = 500

# === Fetch historical data ===
data = fetch_crypto_data(symbol=symbol, timeframe=timeframe, limit=limit)

# === Backtest loop ===
results = {}

for name, model in model_to_run.items():
    print(f"Backtesting: {name}")
    signal, prob, df = model.run_model(data.copy())

    df['Strategy_Return'] = df['Return'] * df['Target']  # Pretend you followed the model
    df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()
    df['Cumulative_BuyHold'] = (1 + df['Return']).cumprod()

    results[name] = df[['Cumulative_Strategy', 'Cumulative_BuyHold']]
    df.to_csv(f'logs/backtest_{name.lower().replace(" ", "_")}.csv')
    
    msg = f"""
    🧪 **Backtest Report: {name}**
    - Final Balance: ${final_balance:.2f}
    - Accuracy: {acc:.2f}
    - Sharpe: {sharpe_ratio:.2f}
    - Strategy Return: {final_return:.2f}x
    - Buy & Hold: {buyhold_return:.2f}x
    """
    send_discord_message(webhook_url, msg)


# === Plotting ===
plt.figure(figsize=(10, 6))
for name, res in results.items():
    plt.plot(res['Cumulative_Strategy'], label=f'{name} (Strategy)')
    plt.plot(res['Cumulative_BuyHold'], '--', label=f'{name} (Buy & Hold)')

plt.title(f'Backtest: {symbol} - {timeframe}')
plt.xlabel('Time')
plt.ylabel('Return (x)')
plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig('logs/backtest_chart.png')
plt.show()

df['Prediction'] = df['Target']  # The model's signal
df['Actual'] = (df['Return'].shift(-1) > 0).astype(int)

# Accuracy
acc = accuracy_score(df['Actual'].dropna(), df['Prediction'].dropna())
final_return = df['Cumulative_Strategy'].iloc[-1]
buyhold_return = df['Cumulative_BuyHold'].iloc[-1]

# Sharpe Ratio
excess_return = df['Strategy_Return'] - df['Return'].mean()
sharpe_ratio = np.mean(excess_return) / np.std(excess_return) * np.sqrt(252)  # annualized

print(f"📊 {name} Summary:")
print(f"  - Accuracy: {acc:.2f}")
print(f"  - Strategy Return: {final_return:.2f}x")
print(f"  - Buy & Hold Return: {buyhold_return:.2f}x")
print(f"  - Sharpe Ratio: {sharpe_ratio:.2f}")

print("✅ Backtest complete. Results saved to /logs/")




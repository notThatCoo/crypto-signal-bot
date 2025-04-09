import pandas as pd
import matplotlib.pyplot as plt
from core.data_fetcher import fetch_crypto_data
from models import logistic_model, random_forest
from sklearn.metrics import accuracy_score
import numpy as np
from core.discord_notifier import send_discord_message

webhook_url = 'https://discord.com/api/webhooks/1357328529653628928/y3o66vxh99SRKjP7RwRz1RTT7ub2WJI8K0qa5i8uTrOu22c9-qidJreGMAUPe3Fzk17F'  # Your real webhook

initial_cash = 1000
symbol = 'BTC/USDT'
timeframe = '1h'
limit = 500

model_to_run = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest
}

# === Fetch data ===
data = fetch_crypto_data(symbol=symbol, timeframe=timeframe, limit=limit)
results = {}

# === Loop through models ===
for name, model in model_to_run.items():
    print(f"Backtesting: {name}")
    signal, prob, df = model.run_model(data.copy())

    # Strategy logic
    df['Strategy_Return'] = df['Return'] * df['Target']
    df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()
    df['Cumulative_BuyHold'] = (1 + df['Return']).cumprod()
    df['Simulated_Balance'] = initial_cash * df['Cumulative_Strategy']

    # Accuracy and Sharpe
    df['Prediction'] = df['Target']
    df['Actual'] = (df['Return'].shift(-1) > 0).astype(int)

    acc = accuracy_score(df['Actual'].dropna(), df['Prediction'].dropna())
    final_return = df['Cumulative_Strategy'].iloc[-1]
    buyhold_return = df['Cumulative_BuyHold'].iloc[-1]
    final_balance = df['Simulated_Balance'].iloc[-1]
    excess_return = df['Strategy_Return'] - df['Return'].mean()
    sharpe_ratio = np.mean(excess_return) / np.std(excess_return) * np.sqrt(252)

    # Save + send
    df.to_csv(f'logs/backtest_{name.lower().replace(" ", "_")}.csv')
    results[name] = df[['Cumulative_Strategy', 'Cumulative_BuyHold']]

    print(f"📊 {name} Summary:")
    print(f"  - Accuracy: {acc:.2f}")
    print(f"  - Strategy Return: {final_return:.2f}x")
    print(f"  - Buy & Hold Return: {buyhold_return:.2f}x")
    print(f"  - Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"💰 Final balance: ${final_balance:.2f}")

    msg = f"""
🧪 **Backtest Report: {name}**
- Final Balance: ${final_balance:.2f}
- Accuracy: {acc:.2f}
- Sharpe: {sharpe_ratio:.2f}
- Strategy Return: {final_return:.2f}x
- Buy & Hold: {buyhold_return:.2f}x
"""
    send_discord_message(webhook_url, msg)

# === Plot ===
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

print("✅ Backtest complete. Results saved to /logs/")




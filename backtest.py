import pandas as pd
import matplotlib.pyplot as plt
from core.data_fetcher import fetch_crypto_data
from models import logistic_model, random_forest

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

print("✅ Backtest complete. Results saved to /logs/")

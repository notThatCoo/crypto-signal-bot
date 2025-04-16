from core.kraken_client import get_balance, get_price

print("🔍 Fetching Kraken account info...")

# Print account balance
balance = get_balance()

# Try both USD and USDT since Kraken supports multiple stable coins
usd_balance = balance['total'].get('USD', 0)
usdt_balance = balance['total'].get('USDT', 0)

print(f"USD Balance: {usd_balance}")
print(f"USDT Balance: {usdt_balance}")

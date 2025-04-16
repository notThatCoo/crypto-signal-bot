from core.kraken_client import get_balance, get_price

print("🔍 Fetching Kraken account info...")

# Print account balance
balance = get_balance()
print("Balance:", balance['total'])

# Print current BTC/USDT price
price = get_price('BTC/USDT')
print("Current BTC/USDT price:", price)

print("Full Balance Breakdown:")
for currency, amount in balance['total'].items():
    print(f"{currency}: {amount}")

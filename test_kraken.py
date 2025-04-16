from core.kraken_client import get_balance, get_price

print("🔍 Fetching Kraken account info...")

# Print account balance
balance = get_balance()
print("Balance:", balance['total'])

# Print current BTC/USDT price
price = get_price('BTC/USDT')
print("Current BTC/USDT price:", price)

dollar_value = btc_amount * price

dollar_value = btc_amount * price

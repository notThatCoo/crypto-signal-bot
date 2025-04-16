from core.kraken_client import get_balance, get_price
from core.kraken_client import place_market_order

print("🔍 Fetching Kraken account info...")

# Print account balance
balance = get_balance()
print("Balance:", balance['total'])
btc_amount = balance['total'].get('BTC', 0)


# Print current BTC/USDT price
price = get_price('BTC/USDT')
print("Current BTC/USDT price:", price)



dollar_value = btc_amount * price

print(f"Dollar amount: ${dollar_value:.2f}")
# order = place_market_order('BTC/USDT', 'buy', 0.0001)
# print("Order result:", order)

print("Available balance:", balance['free'])  # This shows usable funds


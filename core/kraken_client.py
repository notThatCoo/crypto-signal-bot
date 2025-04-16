import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

kraken = ccxt.kraken({
    'apiKey': os.getenv('KRAKEN_API_KEY'),
    'secret': os.getenv('KRAKEN_SECRET_KEY'),
    'enableRateLimit': True
})

def get_balance():
    return kraken.fetch_balance()

def place_market_order(symbol, side, amount):
    return kraken.create_market_order(symbol, side, amount)

def get_price(symbol='BTC/USDT'):
    ticker = kraken.fetch_ticker(symbol)
    return ticker['last']

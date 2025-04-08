import ccxt
import pandas as pd
from datetime import datetime, timedelta

def fetch_crypto_data(symbol='BTC/USDT', timeframe='1h', limit=500):
    exchange = ccxt.kraken()  # or binance if accessible
    since = exchange.milliseconds() - limit * 60 * 60 * 1000  # hours → ms

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df[['close']]

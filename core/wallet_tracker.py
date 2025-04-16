import pandas as pd
from datetime import datetime
import os

class Wallet:
    def __init__(self, starting_cash=1000):
        self.cash = starting_cash
        self.crypto = 0.0
        self.short_position = 0.0
        self.last_trade_price = None
        self.history = []

    def buy(self, price, timestamp, model, prob):
        self.crypto = self.cash / price
        self.cash = 0.0
        self.last_trade_price = price
        self.history.append((timestamp, "BUY", price, model, prob))

    def sell(self, price, timestamp, model, prob):
        self.cash = self.crypto * price
        self.crypto = 0.0
        self.last_trade_price = price
        self.history.append((timestamp, "SELL", price, model, prob))

    def short(self, price, timestamp, model, prob):
        self.short_position = self.cash / price
        self.cash = 0.0
        self.last_trade_price = price
        self.history.append((timestamp, "SHORT", price, model, prob))

    def cover(self, price, timestamp, model, prob):
        pnl = self.short_position * (self.last_trade_price - price)
        self.cash = self.short_position * self.last_trade_price + pnl
        self.short_position = 0.0
        self.last_trade_price = price
        self.history.append((timestamp, "COVER", price, model, prob))

    def value(self, current_price):
        if self.crypto > 0.0:
            return self.crypto * current_price
        elif self.short_position > 0.0:
            pnl = self.short_position * (self.last_trade_price - current_price)
            return self.short_position * self.last_trade_price + pnl
        else:
            return self.cash

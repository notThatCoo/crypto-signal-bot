import pandas as pd
from datetime import datetime
import os

class Wallet:
    def __init__(self, starting_cash=1000, fee=0.001, leverage=1, log_path="logs/live_trades.csv"):
        self.cash = starting_cash
        self.crypto = 0.0
        self.fee = fee
        self.leverage = leverage
        self.log_path = log_path
        self.last_price = None
        self.log_header_written = os.path.exists(self.log_path)

    def buy(self, price, timestamp, model, prob):
        self.last_price = price
        cost = self.cash * self.leverage
        fee_cost = cost * self.fee
        quantity = (cost - fee_cost) / price

        self.cash -= cost  # fully deploy cash
        self.crypto += quantity

        self._log_trade("BUY", price, quantity, fee_cost, model, prob, timestamp)

    def sell(self, price, timestamp, model, prob):
        self.last_price = price
        proceeds = self.crypto * price
        fee_cost = proceeds * self.fee

        self.cash += (proceeds - fee_cost)
        quantity = self.crypto
        self.crypto = 0.0

        self._log_trade("SELL", price, quantity, fee_cost, model, prob, timestamp)

    def value(self, current_price):
        return self.cash + self.crypto * current_price

    def _log_trade(self, action, price, quantity, fee, model, prob, timestamp):
        row = pd.DataFrame([{
            "timestamp": timestamp,
            "action": action,
            "price": round(price, 2),
            "quantity": round(quantity, 6),
            "fee": round(fee, 4),
            "cash": round(self.cash, 2),
            "crypto": round(self.crypto, 6),
            "total_value": round(self.value(price), 2),
            "model": model,
            "signal_prob": round(prob, 4)
        }])
        row.to_csv(self.log_path, mode='a', header=not self.log_header_written, index=False)
        self.log_header_written = True

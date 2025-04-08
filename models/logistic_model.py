import pandas as pd
from sklearn.linear_model import LogisticRegression

def run_model(data):
    # Add features
    data['SMA_5'] = data['close'].rolling(5).mean()
    data['SMA_20'] = data['close'].rolling(20).mean()
    data['Return'] = data['close'].pct_change()
    data.dropna(inplace=True)

    # Target: will price go up next candle?
    data['Target'] = (data['Return'].shift(-1) > 0).astype(int)
    data.dropna(inplace=True)

    # Features and target
    X = data[['SMA_5', 'SMA_20', 'Return']]
    y = data['Target']

    # Train
    model = LogisticRegression()
    model.fit(X[:-1], y[:-1])

    # Predict for the latest row
    latest_features = X.iloc[[-1]]
    prob = model.predict_proba(latest_features)[0][1]
    signal = int(prob > 0.5)

    return signal, prob

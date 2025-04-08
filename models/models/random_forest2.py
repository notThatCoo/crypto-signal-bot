import pandas as pd
from sklearn.ensemble import RandomForestClassifier

def run_model(data):
    data['SMA_5'] = data['close'].rolling(5).mean()
    data['SMA_20'] = data['close'].rolling(20).mean()
    data['Return'] = data['close'].pct_change()
    data['Volatility'] = data['Return'].rolling(10).std()
    data['Momentum'] = data['close'] - data['close'].shift(10)
    data.dropna(inplace=True)

    data['Target'] = (data['Return'].shift(-1) > 0).astype(int)
    data.dropna(inplace=True)

    X = data[['SMA_5', 'SMA_20', 'Return', 'Volatility', 'Momentum']]
    y = data['Target']

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X[:-1], y[:-1])

    latest_features = X.iloc[[-1]]
    prob = model.predict_proba(latest_features)[0][1]
    signal = int(prob > 0.5)

    return signal, prob

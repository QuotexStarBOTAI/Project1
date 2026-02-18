import pandas as pd
import numpy as np
from datetime import datetime, timedelta

rows = 1000
price = 100

data = []

start_time = datetime(2026, 1, 1, 0, 0)

for i in range(rows):
    open_price = price
    change = np.random.uniform(-0.5, 0.5)
    close_price = open_price + change
    high_price = max(open_price, close_price) + np.random.uniform(0, 0.3)
    low_price = min(open_price, close_price) - np.random.uniform(0, 0.3)

    data.append([
        start_time + timedelta(minutes=i),
        round(open_price, 5),
        round(high_price, 5),
        round(low_price, 5),
        round(close_price, 5)
    ])

    price = close_price

df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])
df.to_csv("data.csv", index=False)

print("✅ 1000 candles generated successfully!")

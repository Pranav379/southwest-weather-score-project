import pandas as pd

df = pd.read_csv("Dashboard/processed_flight_data.csv")
df.to_csv("flight_data.csv.gz", index = False, compression = 'gzip')
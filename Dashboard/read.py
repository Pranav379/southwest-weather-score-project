import pandas as pd

df = pd.read_csv("Dashboard/exported_df.csv")
df.to_csv("reduced_exported_df.csv.gz", index=False, compression="gzip")
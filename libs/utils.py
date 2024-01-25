import pandas as pd
from datetime import datetime

def print_error(msg):
    print(f"\033[93m{msg}")

def print_success(msg):
    print(f"\033[92m{msg}")

def status(df, n=5):
    print(f"Shape: {df.shape}")
    return df.head(n)

def load_bq_df(path, date=True):
    if date:
        data = pd.read_csv(path, parse_dates=["event_date"], date_parser=pd.to_datetime, index_col="Unnamed: 0", dtype=str)
    else:
        data = pd.read_csv(path, index_col="Unnamed: 0")
    return data

def create_device_report(df, metric = "impressions", device_col = "device_category", start="2000-01-01", end="2000-01-01"):
    group = df[[device_col, metric]].groupby(device_col).sum()
    group["% of total"] = group[metric].apply(lambda x: (x / group[metric].sum()) * 100)
    group["start_date"] = start
    group["end_date"] = end
    group.reset_index(inplace=True)
    return group
import os, re, json
import numpy as np
import pandas as pd

from scipy import stats
from datetime import datetime
from sklearn.preprocessing import StandardScaler

def output_df_to_csv(df, name):
    output_path = get_output_path()
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    df.to_csv(f"{output_path}/{name}.csv")

# Return relative filepath for processed reports
def get_report_path():
    return "../../output/processed/"

# Calcs % change between 2 values
def calc_delta(control_value, variant_value):
    return ((variant_value - control_value) / control_value) * 100

# Calcs % change between each value and the first value
def calc_deltas(series):
    deltas = [] 
    for x in range(0, series.shape[0]):
        delta = calc_delta(series.iloc[0], series.iloc[x])
        deltas.append(delta)
    return deltas

# Calcs the rate and delta of specifed col (numerator) and returns new df
def calc_rate_and_delta(df, numerator,  divisor):
    processed = df.copy()
    processed[f"{numerator} Rate"] = (processed[numerator] / processed[divisor]) * 100
    processed[f"{numerator} Diff"] = calc_deltas(processed[f"{numerator} Rate"])
    return processed

# Return all processed report file names
def get_processed_report_names():
    files = next(os.walk(get_report_path()), (None, None, []))[2]  # [] if no file
    processed_reports = []
    for file in files:
        if ".csv" in file:
            processed_reports.append(file)
    return processed_reports

# Returns single DataFrame of all reports that match a specified name
def load_reports(name, current_version_only = True):
    processed_report_names = get_processed_report_names()
    relevant_reports = []

    if current_version_only:
        version_str = get_version_str()
        name = f"{version_str}_{name}"

    for processed_report in processed_report_names:
        if f"{name}.csv" in processed_report:
            relevant_reports.append(processed_report)

    master_report = None
    for report in relevant_reports:
        df = pd.read_csv(f"{get_report_path()}{report}", parse_dates=["Date"], date_parser=lambda x: datetime.strptime(x, "%Y%m%d") )
        if isinstance(master_report, pd.DataFrame):
            master_report = pd.concat([master_report, df])
        else:
            master_report = df
    return master_report

# Returens variant name
def determine_variant(dimension):
    if "Control" in dimension:
        return "Control"
    else:
        return re.search("Variation ([0-9]|\.)*", dimension).group()

# Remove outliers from DataFrame
def remove_outliers(df, col, quant=0.99):
    q_low = df[col].quantile(1 - quant)
    q_high = df[col].quantile(quant)
    return df[(df[col] < q_high) & (df[col] > q_low)]

# Removes rows from DataFrame that contain lower than specified value in specified column
def enforce_min_value(df, col, min_value = 0):
    return df[df[col] > min_value].copy()

# Removes rows from DataFrame that contain higher than specified value in specified column
def enforce_max_value(df, col, max_value = 0):
    return df[df[col] < max_value].copy()

# Scales a single column in a DataFrame
def scale_column(df, col):
    scaler = StandardScaler()
    return scaler.fit_transform(df[col].to_numpy().reshape((-1, 1)))

def load_file_as_json(fp):
    file = open(fp, "r")
    json_file = json.load(file)
    return json_file
    
def get_version_str():
    events = load_file_as_json("../../config/events.json")
    metrics = load_file_as_json("../../config/metrics.json")
    segments = load_file_as_json("../../config/segments.json")
    dimensions = load_file_as_json("../../config/dimensions.json")
    boilerplate = load_file_as_json("../../config/boilerplate.json")

    events_version = events["version"]
    dimensions_version = dimensions["version"]
    segments_version = segments["version"]
    metrics_version = metrics["version"]
    boilerplate_version = boilerplate["version"]
    return f"v{boilerplate_version}d{dimensions_version}m{metrics_version}s{segments_version}e{events_version}"


def load_processed_report(name, hasDate = False):
    path = f"{get_output_path()}{name}.csv"
    if hasDate:
        return pd.read_csv(path, parse_dates=["Date"], date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d") )
    else:
        return pd.read_csv(path)

# Return relative filepath for processed reports
def get_output_path():
    return "./processed/"
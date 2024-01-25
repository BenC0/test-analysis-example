import os, datetime
import pandas as pd

def run_and_return(query, name):
    print(f"Running query for {name}")
    df = pd.read_gbq(query=query, progress_bar_type="tqdm", project_id="petsathome-analytics-service")
    print(f"Query complete for {name}")
    return df

def get_query(path):
    with open(path, 'r') as file:
        query = file.read()
        return query
    
def get_local_data(path):
    df = pd.read_csv(path, parse_dates=["event_date"], date_parser=pd.to_datetime, index_col="Unnamed: 0")
    return df

def process_query(query, start_date, end_date):
    processed_query = query
    processed_query = processed_query.replace("{{ @START_DATE }}", '"' + start_date + '"')
    processed_query = processed_query.replace("{{ @END_DATE }}", '"' + end_date + '"')
    return processed_query

def update_local_data(query_name, TEST_start_date="2023-04-24", TEST_ID = "pah000"):
    data_dir = f"./data/"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    query_dir = "../sql/"
    if not os.path.exists(query_dir):
        os.makedirs(query_dir)
    
    query_output_path = data_dir + query_name + ".csv"
    query = get_query(query_dir + query_name + ".sql")

    if os.path.exists(query_output_path):
        local_data = get_local_data(query_output_path)
        most_recent_date = local_data.event_date.max()
        start_date = (most_recent_date + datetime.timedelta(days=1))
    else:
        start_date = datetime.datetime.strptime(TEST_start_date, "%Y-%m-%d")

    yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    if start_date < yesterday:
        end_date_str = yesterday.strftime('%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d')
        processed_query = process_query(query, start_date_str, end_date_str)
        data = run_and_return(processed_query, query_name)
        if os.path.exists(query_output_path):
            local_data = get_local_data(query_output_path)
            data = pd.concat([data, local_data], axis=0)
        data.to_csv(query_output_path)
        print(f"Existing '{query_name}' data is now up to date.")
    else:
        print(f"Existing '{query_name}' data is up to date.")
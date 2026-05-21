import pandas as pd

def process_data(data):
    # Example data processing logic
    df = pd.DataFrame(data, columns=['id', 'name'])
    return df.to_dict(orient='records')
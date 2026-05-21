from app.backend.data_processing import process_data
import pandas as pd

def test_process_data():
    data = {'id': [1, 2], 'name': ['Alice', 'Bob']}
    result = process_data(data)
    expected_df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
    assert result == expected_df.to_dict(orient='records')
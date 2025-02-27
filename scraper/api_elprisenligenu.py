from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
import time

def api_get_el_prices():
    """
    Gets power prices in DK2 from elprisenligenu.dk API.
    
    return (pd.DataFrame): DataFrame with timestamp and prices in (kr / kWh).
    """
    for _ in range(5):
        try:
            # Get tomorrow's date in YYYY/MM-DD format
            tomorrow = datetime.now(pytz.timezone('Europe/Copenhagen')) + timedelta(days=1)
            date_str = tomorrow.strftime("%Y/%m-%d")

            # Call API with dynamic date
            url = f"https://www.elprisenligenu.dk/api/v1/prices/{date_str}_DK1.json"
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for bad status codes

            # Convert response to DataFrame
            df = pd.DataFrame(response.json())

            # Convert DKK_per_kWh to price column and time_start to timestamp
            df = df.rename(columns={'DKK_per_kWh': 'price', 'time_start': 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            return df[['timestamp', 'price']]

        except Exception as e:
            print(f"Error fetching prices: {e}")
            time.sleep(10)


if __name__ == "__main__":
    prices_df = api_get_el_prices()
    if prices_df is not None:
        print("Tomorrow's electricity prices:")
        print(prices_df)
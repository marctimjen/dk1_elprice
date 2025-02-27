import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from datetime import datetime, timedelta
import pandas as pd
import pytz

from database.db_handler import DatabaseHandler
from scraper.web_scraper_elspotpriser import web_scape_el_prices
from scraper.api_elprisenligenu import api_get_el_prices
from utils.telegram_func import send_telegram_message
import time

def validate_prices(api_df, web_df, max_diff_threshold=0.5):
    """
    Validate API prices against web-scraped prices
    Returns: bool indicating if prices are valid
    """
    if api_df is None or web_df is None:
        return False

    # Filter both dataframes to only include tomorrow's data
    tomorrow = datetime.now(pytz.timezone('Europe/Copenhagen')).date() + timedelta(days=1)
    api_df = api_df[api_df['timestamp'].dt.date == tomorrow].copy()
    web_df = web_df[web_df['timestamp'].dt.date == tomorrow].copy()
    print(web_df.to_string(index=False))

    # Merge dataframes on timestamp to compare prices
    merged = pd.merge(
        api_df, 
        web_df, 
        on='timestamp', 
        suffixes=('_api', '_web')
    )

    if merged.empty:
        print("No matching timestamps found between API and web prices")
        return False

    # Calculate price differences
    merged["price_diff"] = abs(merged['price_api'] - merged['price_web'])

    print(merged.to_string(index=False))

    # Check if any price difference exceeds threshold
    return merged["price_diff"].max() <= max_diff_threshold

def scrape_prices():
    """
    Get electricity prices for tomorrow, preferring API data but falling back to web data if needed.
    Returns: DataFrame with validated prices
    """
    api_data = None
    web_data = None
    
    # Try to get API prices
    for _ in range(5):
        try:
            api_data = api_get_el_prices()
            print("Successfully retrieved API prices")
            break
        except Exception as e:
            print(f"Failed to get API prices: {e}")
            time.sleep(60)


    # Try to get web prices
    for _ in range(5):
        try:
            web_data = web_scape_el_prices()
            print("Successfully retrieved web prices")
            break
        except Exception as e:
            print(f"Failed to get web prices: {e}")
            time.sleep(60)

    # If we have both sources, validate API prices
    if api_data is not None and web_data is not None:
        if validate_prices(api_data, web_data):
            print("API prices validated successfully")
            return api_data, 'api'
        else:
            print("WARNING: API prices differ significantly from web prices")
            # You might want to log this situation for monitoring
            return api_data, 'api_DIFFER'
    
    # If API prices are available but couldn't be validated
    if api_data is not None:
        print("Using unvalidated API prices (web prices unavailable)")
        return api_data, 'api_unvalidated'
    
    # Fallback to web prices
    if web_data is not None:
        print("Using web prices (API unavailable)")
        return web_data, 'web'
    
    # Both sources failed
    print("Failed to get prices from both sources")
    return None, None

if __name__ == "__main__":
    prices_df, source = scrape_prices()
    if prices_df is not None:
        print("\nTomorrow's electricity prices:")
        print(f"Source: {source}")
        print(prices_df)

        db = DatabaseHandler()
        db.save_prices(prices_df)

        send_telegram_message(f"Got the prices from {source}:\n{prices_df.to_string(index=False)}")
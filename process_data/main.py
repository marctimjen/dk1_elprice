from database.db_handler import DatabaseHandler
from datetime import datetime, timedelta
import pytz

if __name__ == "__main__":
    db = DatabaseHandler()
    # Use Copenhagen timezone for correct date handling
    copenhagen_tz = pytz.timezone('Europe/Copenhagen')
    tomorrow = (datetime.now(copenhagen_tz) + timedelta(days=1)).date()
    tomorrow_prices = db.get_latest_prices(target_date=tomorrow)
    print(f"Prices for {tomorrow}:")
    print(tomorrow_prices)
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytz
# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from database.db_handler import DatabaseHandler



if __name__ == "__main__":
    db = DatabaseHandler()
    # Use Copenhagen timezone for correct date handling
    copenhagen_tz = pytz.timezone('Europe/Copenhagen')
    tomorrow = (datetime.now(copenhagen_tz) + timedelta(days=1)).date()
    tomorrow_prices = db.get_latest_prices(target_date=tomorrow)
    print(f"Prices for {tomorrow}:")
    print(tomorrow_prices)
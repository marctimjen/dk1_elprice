from datetime import datetime

import pandas as pd
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from database.db_handler import DatabaseHandler
import time as timenator

def web_scape_el_prices():
    """
    This script get the power prices in DK1 from the elspotpriser.dk website.

    return (pd.DataFrame): DataFrame with timestamp and prices in (kr / kWh).
    """

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        # Initialize the Chrome WebDriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        # Navigate to the website
        driver.get("https://elspotpriser.dk/")

        # Wait for the table to be populated
        for _ in range(5):
            wait = WebDriverWait(driver, 10)
            table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
            if len(rows) > 0:
                break

            timenator.sleep(10)


        price_data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 2:
                time = cols[0].text.strip()
                price = cols[1].text.strip().replace(' kr / kWh', '')

                try:
                    price_data.append({
                        'timestamp': time,
                        'price': float(price)
                    })
                except ValueError:
                    continue

        driver.quit()

        if price_data:
            df = pd.DataFrame(price_data)
            # Parse the full datetime string directly
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%A, %B %d at %I:%M %p')
            # Set the year to current year since it's missing from the input
            current_year = datetime.now(pytz.timezone('Europe/Copenhagen')).year
            df['timestamp'] = df['timestamp'].apply(lambda x: x.replace(year=current_year))
            # Add timezone information
            df['timestamp'] = df['timestamp'].dt.tz_localize('Europe/Copenhagen')
            return df

        return None

    except Exception as e:
        print(f"Error processing data: {e}")
        if 'driver' in locals():
            driver.quit()
        return None


if __name__ == "__main__":
    prices_df = web_scape_el_prices()
    print("prices")
    if prices_df is not None:
        print("Current electricity prices:")
        print(prices_df)

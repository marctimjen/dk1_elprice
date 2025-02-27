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
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import platform

def web_scrape_windows():
    """Windows version using Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        return scrape_with_driver(driver)
    except Exception as e:
        print(f"Error in Windows scraping: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def web_scrape_linux():
    """Linux version using Firefox"""
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.set_preference("general.useragent.override", 
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    try:
        driver = webdriver.Firefox(options=firefox_options)
        return scrape_with_driver(driver)
    except Exception as e:
        print(f"Error in Linux scraping: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def scrape_with_driver(driver):
    """Common scraping logic for both platforms"""
    try:
        driver.get("https://elspotpriser.dk/")

        for _ in range(5):
            wait = WebDriverWait(driver, 10)
            table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
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
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%A, %B %d at %I:%M %p')
            current_year = datetime.now(pytz.timezone('Europe/Copenhagen')).year
            df['timestamp'] = df['timestamp'].apply(lambda x: x.replace(year=current_year))
            df['timestamp'] = df['timestamp'].dt.tz_localize('Europe/Copenhagen')
            return df

        return None

    except Exception as e:
        print(f"Error in common scraping: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def web_scape_el_prices():
    """Platform-specific entry point"""
    system = platform.system().lower()
    if system == 'windows':
        return web_scrape_windows()
    elif system == 'linux':
        return web_scrape_linux()
    else:
        raise NotImplementedError(f"No scraper implementation for {system}")

if __name__ == "__main__":
    prices_df = web_scape_el_prices()
    print("prices")
    if prices_df is not None:
        print("Current electricity prices:")
        print(prices_df)

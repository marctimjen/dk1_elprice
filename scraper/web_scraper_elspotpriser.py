import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import locale
import platform
import time as timenator
from datetime import datetime

import pandas as pd
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


system = platform.system().lower()
if system == 'windows':
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
elif system == 'linux':
    def web_scape_el_prices():
        """
        This script get the power prices in DK1 from the elspotpriser.dk website.

        return (pd.DataFrame): DataFrame with timestamp and prices in (kr / kWh).
        """
        # Try different Danish locale variations
        danish_locales = ['da_DK.UTF-8', 'da_DK.utf8', 'da_DK', 'da']
        locale_set = False
        
        for danish_locale in danish_locales:
            try:
                locale.setlocale(locale.LC_TIME, danish_locale)
                locale_set = True
                break
            except locale.Error:
                continue

        # Setup Firefox options
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.set_preference("general.useragent.override",
                                       "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        try:
            # Initialize the Chrome WebDriver
            service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
            driver = webdriver.Firefox(
                service=service,
                options=firefox_options
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
                
                # Different parsing approach based on whether locale was set
                try:
                    if locale_set:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%A, %d %B at %H:%M')
                    else:
                        # Fallback parsing method: manually handle the date parts
                        def parse_date(date_str):
                            # Expected format: "Friday, 28 February at 23:00"
                            parts = date_str.replace(',', '').split()
                            day = int(parts[1])
                            month = parts[2]
                            time_parts = parts[4].split(':')
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                            
                            # Map Danish month names to numbers if needed
                            month_map = {
                                'januar': 1, 'februar': 2, 'marts': 3, 'april': 4,
                                'maj': 5, 'juni': 6, 'juli': 7, 'august': 8,
                                'september': 9, 'oktober': 10, 'november': 11, 'december': 12
                            }
                            
                            month_num = month_map.get(month.lower(), 1)  # Default to January if not found
                            current_year = datetime.now(pytz.timezone('Europe/Copenhagen')).year
                            
                            return datetime(current_year, month_num, day, hour, minute)
                        
                        df['timestamp'] = df['timestamp'].apply(parse_date)

                    # Add timezone information
                    df['timestamp'] = df['timestamp'].dt.tz_localize('Europe/Copenhagen')
                    
                    # Reset locale if it was set
                    if locale_set:
                        locale.setlocale(locale.LC_TIME, '')
                        
                    return df

                except Exception as e:
                    print(f"Error parsing dates: {e}")
                    if locale_set:
                        locale.setlocale(locale.LC_TIME, '')
                    return None

            return None

        except Exception as e:
            print(f"Error processing data: {e}")
            if 'driver' in locals():
                driver.quit()
            return None
else:
    raise NotImplementedError(f"No scraper implementation for {system}")


if __name__ == "__main__":
    prices_df = web_scape_el_prices()
    print("prices")
    if prices_df is not None:
        print("Current electricity prices:")
        print(prices_df)

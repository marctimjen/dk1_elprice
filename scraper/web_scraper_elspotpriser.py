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
        print("Starting web scraping on Linux...")

        # Setup Firefox options
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.set_preference("general.useragent.override",
                                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        try:
            print("Initializing Firefox webdriver...")
            service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
            driver = webdriver.Firefox(
                service=service,
                options=firefox_options
            )

            print("Navigating to elspotpriser.dk...")
            driver.get("https://elspotpriser.dk/")

            price_data = []
            table_found = False

            # Month mapping (both English and Danish)
            month_map = {
                'januar': 1, 'january': 1,
                'februar': 2, 'february': 2,
                'marts': 3, 'march': 3,
                'april': 4, 'april': 4,
                'maj': 5, 'may': 5,
                'juni': 6, 'june': 6,
                'juli': 7, 'july': 7,
                'august': 8, 'august': 8,
                'september': 9, 'september': 9,
                'oktober': 10, 'october': 10,
                'november': 11, 'november': 11,
                'december': 12, 'december': 12
            }

            # Wait for the table to be populated
            for attempt in range(5):
                try:
                    print(f"Attempt {attempt + 1} to find price table...")
                    wait = WebDriverWait(driver, 10)
                    table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
                    if len(rows) > 0:
                        table_found = True
                        print(f"Found {len(rows)} rows of price data")
                        break
                    print("Table found but no rows")
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    timenator.sleep(10)

            if not table_found:
                print("Failed to find price table after all attempts")
                driver.quit()
                return None

            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        time_str = cols[0].text.strip()
                        price = cols[1].text.strip().replace(' kr / kWh', '')
                        
                        # Print raw data for debugging
                        print(f"Raw time string: {time_str}")
                        print(f"Raw price: {price}")

                        try:
                            # Parse the date string manually
                            # Expected format: "Day, DD Month at HH:MM" (in English or Danish)
                            parts = time_str.replace(',', '').split()
                            day = int(parts[1])
                            month = parts[2].lower()
                            time_parts = parts[4].split(':')
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                            
                            month_num = month_map.get(month, 1)
                            current_year = datetime.now(pytz.timezone('Europe/Copenhagen')).year
                            
                            timestamp = datetime(current_year, month_num, day, hour, minute)
                            price_value = float(price)

                            price_data.append({
                                'timestamp': timestamp,
                                'price': price_value
                            })
                            print(f"Parsed datetime: {timestamp}, price: {price_value}")

                        except (ValueError, IndexError) as e:
                            print(f"Error parsing row data: {e}")
                            continue

                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue

            driver.quit()

            if price_data:
                df = pd.DataFrame(price_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['timestamp'] = df['timestamp'].dt.tz_localize('Europe/Copenhagen')
                print(f"Final DataFrame:\n{df}")
                return df

            return None

        except Exception as e:
            print(f"Critical error in web scraping: {str(e)}")
            import traceback
            print(traceback.format_exc())
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

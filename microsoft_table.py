""" File for scraping Windows Server release tables from the Microsoft Wiki page."""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import datetime
import time

class WindowsServerScraper:
    """Scraper class to extract Windows Server tables from the Microsoft Wiki page."""
    def __init__(self, driver_path="./chromedriver.exe", headless=True):
        self.driver_path = driver_path
        self.headless = headless
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.tables_data = {}
        self.output_folder = "output"
        os.makedirs(self.output_folder, exist_ok=True)

    def _setup_driver(self):
        """Initialize and configure the Selenium WebDriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--log-level=3")
        service = Service(self.driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    def open_website(self, url):
        """Opens the given website URL."""
        self.driver.get(url)
        time.sleep(2)

    def expand_sections(self):
        """Expands all collapsible sections on the webpage."""
        sections = self.driver.find_elements(By.XPATH, "//details/summary")
        for section in sections:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", section)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", section)
                time.sleep(3)
            except Exception as e:
                print(f"❌ Could not expand section: {e}")
        time.sleep(3)

    def format_date(self, text):
        """Formats date strings to yyyymmdd format if possible."""
        try:
            parsed_date = datetime.datetime.strptime(text, "%B %d, %Y")
            return parsed_date.strftime("%Y%m%d")
        except ValueError:
            return text  

    def extract_tables(self):
        """Extracts tables from the webpage and stores them in a structured dictionary."""
        tables = self.driver.find_elements(By.XPATH, "//table")

        for idx, table in enumerate(tables):
            try:
                rows = table.find_elements(By.XPATH, ".//tr")
                table_data = []

                for row_idx, row in enumerate(rows):
                    cols = row.find_elements(By.XPATH, ".//th" if row_idx == 0 else ".//td")
                    formatted_cols = [self.format_date(col.text.strip()) for col in cols]

                    if formatted_cols:
                        table_data.append(formatted_cols)

                if table_data:
                    column_titles = tuple(table_data[0])  # Use column headers as key
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])  # Exclude header row from data

                    if column_titles in self.tables_data:
                        self.tables_data[column_titles].append(df)
                    else:
                        self.tables_data[column_titles] = [df]

            except Exception as e:
                print(f"⚠ Error extracting table {idx+1}: {e}")

    def save_to_csv(self):
        """Saves each table with a unique column structure to a separate CSV file."""
        for idx, (columns, dfs) in enumerate(self.tables_data.items()):
            final_df = pd.concat(dfs, ignore_index=True)
            filename = f"windows_server_updates_{idx+1}.csv"
            csv_path = os.path.join(self.output_folder, filename)
            final_df.to_csv(csv_path, index=False)
            print(f"✅ Data saved to '{csv_path}'.")

    def close_driver(self):
        """Closes the Selenium WebDriver."""
        self.driver.quit()

# Usage
scraper = WindowsServerScraper()
scraper.open_website("https://learn.microsoft.com/en-us/windows/release-health/windows-server-release-info")
scraper.expand_sections()
scraper.extract_tables()
scraper.save_to_csv()
scraper.close_driver()

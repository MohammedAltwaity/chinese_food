from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pathlib import Path
from bs4 import BeautifulSoup
import sys

if len(sys.argv) < 2:
    print("Usage: python saucenao.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]

options = Options()
# Do not run headless
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.get('https://saucenao.com/')

print("Opened SauceNAO. Waiting 3 seconds for page to load...")
time.sleep(3)

try:
    upload_input = driver.find_element(By.ID, 'fileInput')
    upload_input.send_keys(str(Path(image_path).absolute()))
    print(f"Uploaded {image_path} to SauceNAO. Waiting 2 seconds before submitting...")
    time.sleep(2)
    search_button = driver.find_element(By.ID, 'searchButton')
    search_button.click()
    print("Submitted search. Waiting 10 seconds for results...")
    time.sleep(10)

    # Parse results with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = soup.find_all('div', class_='result')
    found = False
    for result in results:
        author_strong = result.find('strong', string='Author: ')
        if author_strong:
            author_link = author_strong.find_next('a')
            if author_link:
                print(f"Author: {author_link.text.strip()}")
                found = True
    if not found:
        print("No authors found in results.")
except Exception as e:
    print(f"Error during upload/search: {e}")

input("Browser is open. Press Enter to close...")
driver.quit() 
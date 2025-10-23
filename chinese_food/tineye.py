from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pathlib import Path
from bs4 import BeautifulSoup
import sys

if len(sys.argv) < 2:
    print("Usage: python tineye.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]

options = Options()
# Do not run headless
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.get('https://tineye.com/')

print("Opened TinEye. Waiting 3 seconds for page to load...")
time.sleep(3)

try:
    upload_input = driver.find_element(By.ID, 'upload-box')
    upload_input.send_keys(str(Path(image_path).absolute()))
    print(f"Uploaded {image_path} to TinEye. Waiting 2 seconds before submitting...")
    time.sleep(2)
    # TinEye auto-submits after upload, so just wait for results
    print("Waiting 10 seconds for results...")
    time.sleep(10)

    # Parse results with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Get number of results
    result_count = soup.find('div', class_='match-count')
    if result_count:
        print(result_count.text.strip())
    else:
        print("Could not find result count.")
    # Get website and URLs of first few matches
    matches = soup.find_all('h4', attrs={'data-test': 'match-title'})
    if not matches:
        # fallback: try to find by class if data-test is not present
        matches = soup.find_all('h4', class_='text-base pb-1 max-[450px]:text-sm')
    if matches:
        for idx, h4 in enumerate(matches, 1):
            a = h4.find('a', href=True)
            if a:
                print(f"Website: {a.text.strip()}")
                print(f"URL: {a['href']}")
    else:
        print("No matches found.")
except Exception as e:
    print(f"Error during upload/search: {e}")

input("Browser is open. Press Enter to close...")
driver.quit() 
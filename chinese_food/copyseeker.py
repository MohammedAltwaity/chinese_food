from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pathlib import Path
from bs4 import BeautifulSoup
import sys

if len(sys.argv) < 2:
    print("Usage: python copyseeker.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]

options = Options()
# Do not run headless
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.get('https://copyseeker.net/')

print("Opened Copyseeker. Waiting 3 seconds for page to load...")
time.sleep(3)

# Try to accept cookies if the dialog appears
try:
    accept_btn = driver.find_element(By.XPATH, '//button[contains(text(), "Accept")]')
    accept_btn.click()
    print("Accepted cookies.")
    time.sleep(2)
except Exception:
    print("No cookie dialog or could not find Accept button. Proceeding...")

try:
    # Find the file input (type=file, style display:none)
    upload_input = driver.find_element(By.XPATH, '//input[@type="file" and @placeholder="Choose file"]')
    upload_input.send_keys(str(Path(image_path).absolute()))
    print(f"Uploaded {image_path} to Copyseeker. Waiting 2 seconds before submitting...")
    time.sleep(2)
    # The site may auto-submit, so just wait for results
    print("Waiting 30 seconds for results...")
    time.sleep(30)

    # Parse results with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Print all page titles from <p class='web-title'>
    titles = soup.find_all('p', class_='web-title')
    if titles:
        for idx, title in enumerate(titles, 1):
            print(f"Result {idx}: {title.get_text(strip=True)}")
    else:
        print("No page titles found in results.")
except Exception as e:
    print(f"Error during upload/search: {e}")

input("Browser is open. Press Enter to close...")
driver.quit() 
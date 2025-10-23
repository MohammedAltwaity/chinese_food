from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Search4faces automation script')
parser.add_argument('image_path', help='Path to the image file to search')
args = parser.parse_args()

# Validate image path
if not os.path.exists(args.image_path):
    print(f"Error: Image file '{args.image_path}' does not exist.")
    exit(1)

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--incognito")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_argument("--host-resolver-rules=MAP pagead2.googlesyndication.com 127.0.0.1, MAP googleads.g.doubleclick.net 127.0.0.1, MAP tpc.googlesyndication.com 127.0.0.1")

driver = webdriver.Chrome(options=options)
driver.get("https://search4faces.com/en/vk01/index.html")

def extract_card_info(card_element):
    """Extract all information from a card element"""
    try:
        # Extract name
        name = card_element.find_element(By.CSS_SELECTOR, ".card-vk01-header").text.strip()
    except Exception:
        name = "(No name found)"
    
    try:
        # Extract score
        score_element = card_element.find_element(By.CSS_SELECTOR, ".card-vk01-score")
        score = score_element.text.strip()
    except Exception:
        score = "(No score found)"
    
    try:
        # Extract age
        age = card_element.find_element(By.CSS_SELECTOR, ".card-vk01-age").text.strip()
    except Exception:
        age = "(No age found)"
    
    try:
        # Extract location
        location = card_element.find_element(By.CSS_SELECTOR, ".card-vk01-geo").text.strip()
    except Exception:
        location = "(No location found)"
    
    return name, score, age, location

image_path = os.path.abspath(args.image_path)  # Use command line argument
print(f"Using image: {image_path}")

try:
    # Step 1: Click the first upload button
    upload_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "upload-button"))
    )
    upload_btn.click()
    print("Clicked first upload button.")

    # Step 2: Wait for the drag-and-drop area in the pop-up
    drop_area = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "drop-area"))
    )
    print("Drop area is visible.")

    # Drag-and-drop the image file using JS
    with open(image_path, "rb") as f:
        file_data = f.read()
    js_drop_file = '''
    var target = arguments[0];
    var dataTransfer = new DataTransfer();
    var file = new File([new Uint8Array(arguments[1])], arguments[2], {type: 'image/jpeg'});
    dataTransfer.items.add(file);
    var event = new DragEvent('drop', {dataTransfer: dataTransfer});
    target.dispatchEvent(event);
    '''
    driver.execute_script(js_drop_file, drop_area, list(file_data), os.path.basename(image_path))
    print("Drag-and-drop event dispatched.")

    # Step 3: Click the footer upload button in the pop-up
    footer_upload_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.effects-continue--upload"))
    )
    footer_upload_btn.click()
    print("Clicked footer upload button.")

    # Step 4: Wait for redirect to main page and for the search button to appear
    search_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "search-button"))
    )
    print("Search button is visible and clickable.")
    search_btn.click()
    print("Clicked search button.")

    # Step 5: Wait for results to load and try to extract them robustly
    time.sleep(3)
    found_results = False

    # 1. Wait for .card-vk01-header up to 30s
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card-vk01-header"))
        )
        print("Result headers found in main document!")
        # Find all cards (parent containers of .card-vk01-header)
        cards = driver.find_elements(By.XPATH, "//*[contains(@class, 'card') and .//div[contains(@class, 'card-vk01-header')]]")
        if not cards:
            # Fallback: find cards by looking for elements containing .card-vk01-header
            headers = driver.find_elements(By.CSS_SELECTOR, ".card-vk01-header")
            cards = [header.find_element(By.XPATH, "ancestor::*[contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'result')]") for header in headers]
        
        for i, card in enumerate(cards, 1):
            name, score, age, location = extract_card_info(card)
            print(f"{i}. {name}")
            print(f"   Score: {score}")
            print(f"   Age: {age}")
            print(f"   Location: {location}")
            print("-" * 40)
        found_results = True
    except Exception as e:
        print(f"No .card-vk01-header found in main document after waiting: {e}")

    # 2. Print all iframe sources
    if not found_results:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes.")
        for idx, iframe in enumerate(iframes):
            print(f"Iframe {idx}: {iframe.get_attribute('src')}")

        # 3. Try switching to each iframe and searching for .card-vk01-header
        for idx, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                print(f"Switched to iframe {idx}.")
                cards = driver.find_elements(By.XPATH, "//*[contains(@class, 'card') and .//div[contains(@class, 'card-vk01-header')]]")
                if not cards:
                    headers = driver.find_elements(By.CSS_SELECTOR, ".card-vk01-header")
                    cards = [header.find_element(By.XPATH, "ancestor::*[contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'result')]") for header in headers]
                
                if cards:
                    print(f"Found {len(cards)} result cards in iframe {idx}!")
                    for i, card in enumerate(cards, 1):
                        name, score, age, location = extract_card_info(card)
                        print(f"{i}. {name}")
                        print(f"   Score: {score}")
                        print(f"   Age: {age}")
                        print(f"   Location: {location}")
                        print("-" * 40)
                    found_results = True
                driver.switch_to.default_content()
            except Exception as e:
                print(f"Error switching to iframe {idx}: {e}")
            finally:
                driver.switch_to.default_content()

    # 4. Try shadow DOM extraction if still not found
    if not found_results:
        print("Trying shadow DOM extraction...")
        js = '''
        let results = [];
        function findCards(node) {
            if (node.shadowRoot) {
                let cards = node.shadowRoot.querySelectorAll('*[class*="card"]');
                cards.forEach(card => {
                    let name = card.querySelector('.card-vk01-header')?.textContent || '(No name)';
                    let score = card.querySelector('.card-vk01-score')?.textContent || '(No score)';
                    let age = card.querySelector('.card-vk01-age')?.textContent || '(No age)';
                    let location = card.querySelector('.card-vk01-geo')?.textContent || '(No location)';
                    results.push({name, score, age, location});
                });
                node.shadowRoot.childNodes.forEach(findCards);
            }
            node.childNodes.forEach(findCards);
        }
        findCards(document);
        return results;
        '''
        try:
            shadow_results = driver.execute_script(js)
            if shadow_results:
                print(f"Found {len(shadow_results)} result cards in shadow DOM!")
                for i, result in enumerate(shadow_results, 1):
                    print(f"{i}. {result['name'].strip()}")
                    print(f"   Score: {result['score'].strip()}")
                    print(f"   Age: {result['age'].strip()}")
                    print(f"   Location: {result['location'].strip()}")
                    print("-" * 40)
                found_results = True
            else:
                print("No result cards found in shadow DOM.")
        except Exception as e:
            print(f"Error extracting from shadow DOM: {e}")

    if not found_results:
        print("No result cards found. Trying to print all text on page.")
        print(driver.find_element(By.TAG_NAME, "body").text)

except Exception as e:
    print("Error:", e)
finally:
    input("Press Enter to quit and close browser...")
    driver.quit()
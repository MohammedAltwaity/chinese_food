import sys
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import os

class FaceCheckManualAssist:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        try:
            options = Options()
            
            # Stealth options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Realistic window size
            options.add_argument('--window-size=1920,1080')
            
            # Realistic user agent
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            options.add_argument(f'--user-agent={user_agent}')
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Driver setup successful")
            
        except Exception as e:
            print(f"Failed to setup driver: {e}")
            raise
    
    def human_like_delay(self, min_delay=0.5, max_delay=1.5):
        """Add human-like random delays (optimized for speed)"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior"""
        # Random mouse movements
        actions = ActionChains(self.driver)
        for _ in range(random.randint(2, 4)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.3))
        actions.perform()
        
        # Random scrolling
        scroll_amount = random.randint(-100, 100)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self.human_like_delay(0.5, 1.5)
    
    def simulate_screen_behavior(self):
        """Simulate minimize/fullscreen behavior like in PimEyes script"""
        try:
            print("Simulating screen minimize/fullscreen behavior...")
            
            # Minimize window
            self.driver.minimize_window()
            time.sleep(1)  # Quick minimize wait
            
            # Maximize window
            self.driver.maximize_window()
            time.sleep(1)  # Quick maximize wait
            
            print("Screen behavior simulation completed")
            
        except Exception as e:
            print(f"Screen behavior simulation failed: {e}")
    
    def handle_cookie_consent(self):
        """Handle cookie consent popup if present"""
        try:
            print("Looking for cookie consent popup...")
            self.human_like_delay(2, 4)
            
            # Common cookie consent selectors
            cookie_selectors = [
                'button[class*="accept"]',
                'button[class*="allow"]',
                'button[class*="cookie"]',
                'button:contains("Accept")',
                'button:contains("Allow")',
                'button:contains("OK")',
                '[id*="cookie"] button',
                '[class*="cookie"] button'
            ]
            
            for selector in cookie_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.lower()
                            if any(word in text for word in ['accept', 'allow', 'ok', 'agree']):
                                print(f"Found cookie consent button: {element.text}")
                                element.click()
                                self.human_like_delay(1, 2)
                                return True
                except:
                    continue
            
            print("No cookie consent popup found or already handled")
            return False
            
        except Exception as e:
            print(f"Cookie consent handling failed: {e}")
            return False
    
    def upload_image(self, image_path):
        """Upload image using the Browse button"""
        try:
            print("Looking for Browse button...")
            self.human_like_delay(1, 2)  # Reduced wait time
            
            # First, wait for the form to be present
            print("Waiting for form to load...")
            form = self.driver.find_element(By.CSS_SELECTOR, 'form.my-form')
            if not form.is_displayed():
                print("Form not visible")
                return False
            
            # Find the Browse button using the exact selector
            browse_button = self.driver.find_element(By.CSS_SELECTOR, 'label.button.browsebutton[for="fileElem"]')
            
            if browse_button.is_displayed():
                print("Found Browse button, attempting to click...")
                
                # Scroll to button to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", browse_button)
                time.sleep(0.5)  # Quick scroll wait
                
                # Use JavaScript click directly (fastest method)
                try:
                    print("Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", browse_button)
                    print("JavaScript click successful!")
                except Exception as e:
                    print(f"JavaScript click failed: {e}")
                    return False
                
                time.sleep(0.5)  # Quick wait after click
                
                # Find the file input element
                file_input = self.driver.find_element(By.ID, "fileElem")
                
                # Make sure it's visible and accessible
                self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
                self.driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
                self.driver.execute_script("arguments[0].style.opacity = '1';", file_input)
                
                # Upload the file
                file_input.send_keys(str(Path(image_path).absolute()))
                print("File uploaded successfully!")
                
                # Wait for upload to complete
                self.human_like_delay(1, 2)  # Reduced wait time
                return True
            else:
                print("Browse button not found or not visible")
                return False
                
        except Exception as e:
            print(f"Upload failed: {e}")
            return False
    
    def click_search_button(self):
        """Click the Search Internet by Face button"""
        try:
            print("Looking for Search button...")
            time.sleep(0.5)  # Quick wait
            
            # Find the Search button using the exact selector provided
            search_button = self.driver.find_element(By.CSS_SELECTOR, 'button#searchButton.button-24.buttonshiny')
            
            if search_button.is_displayed():
                print("Found Search button, attempting to click...")
                
                # Scroll to button to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                time.sleep(0.3)  # Quick scroll wait
                
                # Use JavaScript click to bypass overlay
                try:
                    print("Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", search_button)
                    print("JavaScript click successful!")
                    
                    time.sleep(0.5)  # Quick wait after click
                    return True
                except Exception as e:
                    print(f"JavaScript click failed: {e}")
                    return False
            else:
                print("Search button not found or not visible")
                return False
                
        except Exception as e:
            print(f"Error clicking search button: {e}")
            return False
    
    def handle_terms_checkbox(self):
        """Handle the terms of use checkbox"""
        try:
            print("Looking for terms checkbox...")
            time.sleep(0.3)  # Quick wait
            
            # Find the checkbox using the exact selector provided
            checkbox = self.driver.find_element(By.CSS_SELECTOR, 'input.form-check-input[type="checkbox"][id="iagree"]')
            
            if checkbox.is_displayed() and checkbox.is_enabled():
                print("Found terms checkbox, checking it...")
                
                # Scroll to checkbox if needed
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                time.sleep(0.2)  # Quick scroll wait
                
                # Use JavaScript click to bypass overlay
                try:
                    print("Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    print("Terms checkbox checked successfully!")
                    
                    time.sleep(0.3)  # Quick wait after click
                    return True
                except Exception as e:
                    print(f"JavaScript click failed: {e}")
                    return False
            else:
                print("Terms checkbox not found or not enabled")
                return False
                
        except Exception as e:
            print(f"Error handling terms checkbox: {e}")
            return False
    
    def click_agree_and_search(self):
        """Click the Agree and Search button"""
        try:
            print("Looking for Agree and Search button...")
            time.sleep(0.3)  # Quick wait
            
            # Find the Agree and Search button using the exact selector provided
            agree_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn.btn-agree')
            
            if agree_button.is_displayed():
                print("Found Agree and Search button, attempting to click...")
                
                # Scroll to button to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", agree_button)
                time.sleep(0.3)  # Quick scroll wait
                
                # Use JavaScript click to bypass overlay
                try:
                    print("Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", agree_button)
                    print("Agree and Search button clicked successfully!")
                    
                    time.sleep(0.5)  # Quick wait after click
                    return True
                except Exception as e:
                    print(f"JavaScript click failed: {e}")
                    return False
            else:
                print("Agree and Search button not found or not visible")
                return False
                
        except Exception as e:
            print(f"Error clicking agree button: {e}")
            return False
    
    def wait_for_captcha(self):
        """Wait for captcha to appear"""
        try:
            print("Waiting for captcha to appear...")
            
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # Look for captcha indicators
                    captcha_indicators = [
                        '[class*="captcha"]',
                        '[class*="slider"]',
                        '[class*="puzzle"]',
                        'div:contains("Verify")',
                        'div:contains("Captcha")',
                        'canvas',
                        'img[src*="captcha"]'
                    ]
                    
                    for selector in captcha_indicators:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed():
                                    print(f"Found captcha indicator: {selector}")
                                    return True
                        except:
                            continue
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error checking for captcha: {e}")
                    time.sleep(1)
            
            print("No captcha detected within timeout")
            return False
            
        except Exception as e:
            print(f"Error waiting for captcha: {e}")
            return False
    
    def manual_captcha_verification(self):
        """Pause for manual captcha verification"""
        print("\n" + "="*50)
        print("MANUAL CAPTCHA VERIFICATION REQUIRED")
        print("="*50)
        print("1. Look for the sliding puzzle captcha")
        print("2. Slide the small image piece into the correct position")
        print("3. Complete the verification")
        print("4. Script will automatically continue after 15 seconds")
        print("="*50)
        
        # Wait 15 seconds for manual captcha completion
        print("Waiting 15 seconds for manual captcha completion...")
        time.sleep(15)
        
        # Simulate Enter key press to continue
        print("Simulating Enter key press to continue...")
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        
        print("Captcha verification completed, continuing...")
        return True
    
    def wait_for_search_completion(self):
        """Wait for search to complete (20 seconds + monitoring)"""
        try:
            print("Waiting for search to complete...")
            
            max_wait = 60  # Extended timeout for search
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # Look for search progress indicators
                    progress_indicators = [
                        'div:contains("Searching faces")',
                        'div:contains("Processing")',
                        'div:contains("%")',
                        '[class*="progress"]',
                        '[class*="loading"]'
                    ]
                    
                    # Look for completion indicators
                    completion_indicators = [
                        '[class*="result"]',
                        '[class*="match"]',
                        '[class*="found"]',
                        'div:contains("Results")',
                        'div:contains("Matches")',
                        'table',
                        '[class*="list"]'
                    ]
                    
                    # Check if still searching
                    still_searching = False
                    for selector in progress_indicators:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed():
                                    text = element.text
                                    if "Searching faces" in text or "%" in text:
                                        print(f"Search progress: {text}")
                                        still_searching = True
                                        break
                            if still_searching:
                                break
                        except:
                            continue
                    
                    # Check if search is complete
                    if not still_searching:
                        for selector in completion_indicators:
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for element in elements:
                                    if element.is_displayed():
                                        print(f"Search complete, found: {element.text[:50]}...")
                                        return True
                            except:
                                continue
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error checking search status: {e}")
                    time.sleep(2)
            
            print("Search timeout reached")
            return False
            
        except Exception as e:
            print(f"Error waiting for search completion: {e}")
            return False
    
    def extract_results(self):
        """Extract search results"""
        try:
            print("Extracting search results...")
            
            # Look for result containers
            result_selectors = [
                '[class*="result"]',
                '[class*="match"]',
                '[class*="found"]',
                'table',
                '[class*="list"]',
                '[class*="item"]',
                'div[class*="card"]',
                'div[class*="profile"]'
            ]
            
            results = []
            for selector in result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and len(text) > 10:  # Meaningful content
                                results.append({
                                    'selector': selector,
                                    'text': text,
                                    'element': element
                                })
                except:
                    continue
            
            if results:
                print(f"Found {len(results)} potential result elements:")
                for i, result in enumerate(results[:5], 1):  # Show first 5
                    print(f"{i}. {result['selector']}: {result['text'][:100]}...")
                return results
            else:
                print("No results found")
                return []
                
        except Exception as e:
            print(f"Error extracting results: {e}")
            return []
    
    def search_facecheck(self, image_path):
        """Main search function for facecheck.id with manual captcha"""
        try:
            print("Starting FaceCheck search with manual captcha assistance...")
            
            self.setup_driver()
            
            print("Navigating to FaceCheck...")
            self.driver.get('http://facecheck.id')
            
            # Wait for page to load completely
            print("Waiting for page to load...")
            self.human_like_delay(2, 3)  # Reduced wait time
            
            # Handle cookie consent
            self.handle_cookie_consent()
            
            # Simulate screen behavior (minimize/fullscreen)
            self.simulate_screen_behavior()
            
            # Debug: Check what elements are present
            print("Checking page elements...")
            try:
                forms = self.driver.find_elements(By.CSS_SELECTOR, 'form.my-form')
                print(f"Found {len(forms)} forms with class 'my-form'")
                
                browse_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'label.button.browsebutton[for="fileElem"]')
                print(f"Found {len(browse_buttons)} browse buttons")
                
                file_inputs = self.driver.find_elements(By.ID, "fileElem")
                print(f"Found {len(file_inputs)} file inputs")
                
            except Exception as e:
                print(f"Error checking elements: {e}")
            
            # Upload image
            if not self.upload_image(image_path):
                print("Failed to upload image")
                return
            
            # Click Search button
            if not self.click_search_button():
                print("Failed to click search button")
                return
            
            # Handle terms checkbox
            if not self.handle_terms_checkbox():
                print("Failed to handle terms checkbox")
                return
            
            # Click Agree and Search
            if not self.click_agree_and_search():
                print("Failed to click agree and search")
                return
            
            # Check for captcha
            if self.wait_for_captcha():
                # Manual captcha verification
                if not self.manual_captcha_verification():
                    print("Manual captcha verification failed")
                    return
            else:
                print("No captcha detected, continuing...")
            
            # Wait for search completion
            if not self.wait_for_search_completion():
                print("Failed to complete search")
                return
            
            # Extract results
            results = self.extract_results()
            
            if results:
                print("Search completed successfully!")
                print("Results extracted and ready for analysis.")
            else:
                print("Search completed but no results found.")
            
        except Exception as e:
            print(f"Error during search: {e}")
        finally:
            input("Press Enter to close browser...")
            if self.driver:
                self.driver.quit()

def main():
    if len(sys.argv) < 2:
        print("Usage: python facecheck_manual_assist.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' does not exist.")
        sys.exit(1)
    
    automation = FaceCheckManualAssist()
    automation.search_facecheck(image_path)

if __name__ == '__main__':
    main() 
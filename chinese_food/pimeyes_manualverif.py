import sys
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pathlib import Path
import os

class PimEyesManualAssist:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with basic stealth"""
        try:
            options = Options()
            
            # Basic stealth options
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
            
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Driver setup successful")
            
        except Exception as e:
            print(f"Failed to setup driver: {e}")
            raise
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add human-like random delays"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def handle_cookie_consent(self):
        """Handle Cookiebot consent popup"""
        try:
            print("Looking for cookie consent popup...")
            self.human_like_delay(2, 4)
            
            allow_button = self.driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            
            if allow_button.is_displayed():
                print("Found cookie consent popup, clicking 'Allow all'")
                allow_button.click()
                self.human_like_delay(1, 2)
                return True
            else:
                print("Cookie popup not found or already handled")
                return False
                
        except Exception as e:
            print(f"Cookie consent handling failed: {e}")
            return False
    
    def simulate_screen_behavior(self):
        """Simulate screen minimize/fullscreen behavior"""
        try:
            print("Simulating screen minimize/fullscreen behavior...")
            
            # First cycle: minimize -> fullscreen
            print("Cycle 1: Minimizing window...")
            self.driver.minimize_window()
            time.sleep(2)
            
            print("Cycle 1: Maximizing window...")
            self.driver.maximize_window()
            time.sleep(2)
            
            # Second cycle: minimize -> fullscreen
            print("Cycle 2: Minimizing window...")
            self.driver.minimize_window()
            time.sleep(2)
            
            print("Cycle 2: Maximizing window...")
            self.driver.maximize_window()
            time.sleep(2)
            
            print("Screen behavior simulation complete")
            
        except Exception as e:
            print(f"Error in screen behavior simulation: {e}")
    
    def close_file_explorer(self):
        """Close file OS explorer dialog using mouse click simulation"""
        try:
            print("Attempting to close file OS explorer with mouse click...")
            
            # Wait a bit for file dialog to appear
            time.sleep(1)
            
            # Method 1: Click outside the dialog area (top-left corner of browser)
            try:
                print("Clicking outside dialog area...")
                actions = ActionChains(self.driver)
                # Click at coordinates (10, 10) - top-left corner
                actions.move_by_offset(10, 10)
                actions.click()
                actions.perform()
                time.sleep(1)
            except Exception as e:
                print(f"Click outside failed: {e}")
            
            # Method 2: Click on browser window title bar area
            try:
                print("Clicking on browser title bar...")
                actions = ActionChains(self.driver)
                # Click at coordinates (100, 5) - title bar area
                actions.move_by_offset(90, -5)  # Move from previous position
                actions.click()
                actions.perform()
                time.sleep(1)
            except Exception as e:
                print(f"Title bar click failed: {e}")
            
            # Method 3: Press Escape key
            try:
                print("Pressing Escape key...")
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
                time.sleep(1)
            except Exception as e:
                print(f"Escape key failed: {e}")
            
            # Method 4: Click on a specific area of the page
            try:
                print("Clicking on page content...")
                # Find a safe area to click (like the main content area)
                main_content = self.driver.find_element(By.TAG_NAME, "body")
                actions = ActionChains(self.driver)
                actions.move_to_element(main_content)
                actions.click()
                actions.perform()
                time.sleep(1)
            except Exception as e:
                print(f"Content click failed: {e}")
            
            print("File explorer close attempts completed")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error closing file explorer: {e}")
    
    def upload_image_manual(self, image_path):
        """Upload image with manual assistance"""
        try:
            print("Looking for upload area...")
            self.human_like_delay(2, 4)
            
            # Simulate screen behavior before upload
            self.simulate_screen_behavior()
            
            # Find the upload area
            upload_selectors = [
                'div[data-v-b0e0b6c4]',
                'div:has(.drop-photos-label)',
                '[class*="upload"]',
                '[class*="drop"]'
            ]
            
            upload_area = None
            for selector in upload_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.lower()
                            if 'upload' in text or 'drop' in text or 'click' in text:
                                upload_area = element
                                print(f"Found upload area with selector: {selector}")
                                break
                    if upload_area:
                        break
                except:
                    continue
            
            if not upload_area:
                print("Upload area not found")
                return False
            
            # Click the upload area
            print("Clicking upload area to trigger file dialog...")
            upload_area.click()
            self.human_like_delay(1, 2)
            
            # Close file OS explorer
            self.close_file_explorer()
            
            # Find file input and upload
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            if file_inputs:
                file_input = file_inputs[0]
                
                # Make sure it's visible
                self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
                self.driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
                
                # Upload the file
                file_input.send_keys(str(Path(image_path).absolute()))
                print("File uploaded successfully!")
                
                # Wait for upload to complete
                self.human_like_delay(2, 4)
                return True
            else:
                print("File input not found after clicking upload area")
                return False
                
        except Exception as e:
            print(f"Upload failed: {e}")
            return False
    
    def wait_for_challenge(self):
        """Wait for Turnstile challenge to appear"""
        try:
            print("Waiting for image processing and challenge...")
            
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # Check for challenge indicators
                    challenge_indicators = [
                        'input[type="checkbox"]',
                        '.cb-lb',
                        '[class*="turnstile"]',
                        '[class*="challenge"]'
                    ]
                    
                    for selector in challenge_indicators:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                print(f"Found challenge indicator: {selector}")
                                return True
                    
                    # Check for success indicators
                    success_indicators = [
                        'button[data-v-6f435614]',
                        'button:contains("Start Search")',
                        '[class*="success"]'
                    ]
                    
                    for selector in success_indicators:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                print("Already past challenge, found success indicator")
                                return True
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error checking challenge status: {e}")
                    time.sleep(1)
            
            print("Timeout waiting for challenge")
            return False
            
        except Exception as e:
            print(f"Error waiting for challenge: {e}")
            return False
    
    def manual_verification(self):
        """Pause for manual verification and simulate Enter press"""
        print("\n" + "="*50)
        print("MANUAL VERIFICATION REQUIRED")
        print("="*50)
        print("1. Look for the 'Verify you are human' checkbox")
        print("2. Click the checkbox manually")
        print("3. Wait for verification to complete (3-5 seconds)")
        print("4. Look for 'Success!' message or terms checkboxes")
        print("5. Script will automatically continue after 10 seconds")
        print("="*50)
        
        # Wait 10 seconds for manual verification, then simulate Enter
        print("Waiting 10 seconds for manual verification...")
        time.sleep(10)
        
        # Simulate Enter key press
        print("Simulating Enter key press to continue...")
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        
        # Check if verification was successful
        success_indicators = [
            'input[data-v-dc978e0d][type="checkbox"]',
            'button[data-v-6f435614]',
            'button:contains("Start Search")',
            '[id="success"]'
        ]
        
        for selector in success_indicators:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        print("Verification successful!")
                        return True
            except:
                continue
        
        print("Verification status unclear, continuing...")
        return True
    
    def handle_terms_checkboxes(self):
        """Handle the 3 required terms checkboxes"""
        try:
            print("Looking for terms and conditions checkboxes...")
            
            # Wait a bit for checkboxes to appear
            self.human_like_delay(2, 4)
            
            # Find all required checkboxes
            checkbox_selectors = [
                'input[data-v-dc978e0d][type="checkbox"][required]',
                'input[data-v-dc978e0d][type="checkbox"]'
            ]
            
            checkboxes = []
            for selector in checkbox_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            checkboxes.append(element)
                    if len(checkboxes) >= 3:
                        break
                except:
                    continue
            
            if len(checkboxes) < 3:
                print(f"Found only {len(checkboxes)} checkboxes, expected 3")
                return False
            
            print(f"Found {len(checkboxes)} checkboxes, checking them...")
            
            # Check each checkbox
            for i, checkbox in enumerate(checkboxes[:3], 1):
                try:
                    print(f"Checking checkbox {i}...")
                    
                    # Scroll to checkbox if needed
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    self.human_like_delay(0.5, 1)
                    
                    # Click the checkbox
                    checkbox.click()
                    print(f"Checkbox {i} checked successfully")
                    
                    # Small delay between checkboxes
                    self.human_like_delay(0.5, 1)
                    
                except Exception as e:
                    print(f"Error checking checkbox {i}: {e}")
                    return False
            
            print("All 3 checkboxes checked successfully!")
            self.human_like_delay(1, 2)
            return True
            
        except Exception as e:
            print(f"Error handling terms checkboxes: {e}")
            return False
    
    def click_start_search(self):
        """Click the Start Search button"""
        try:
            print("Looking for Start Search button...")
            
            # Wait a bit for button to appear after checkboxes
            self.human_like_delay(2, 4)
            
            # More specific selectors for the Start Search button
            search_button_selectors = [
                'button[data-v-6f435614]',
                'button[data-v-6f435614] span[data-v-6f435614]',
                'button:has(span:contains("Start Search"))',
                'button span:contains("Start Search")'
            ]
            
            search_button = None
            for selector in search_button_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            # Check if it's the button or span
                            if element.tag_name == 'button':
                                text = element.text.lower()
                            else:  # span element
                                text = element.text.lower()
                                # Get the parent button
                                element = element.find_element(By.XPATH, './..')
                            
                            if 'start search' in text:
                                search_button = element
                                print(f"Found search button with selector: {selector}")
                                break
                    if search_button:
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not search_button:
                print("Start Search button not found, trying alternative approach...")
                
                # Alternative: find by text content
                try:
                    # Find all buttons and check their text
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in all_buttons:
                        if button.is_displayed():
                            text = button.text.lower()
                            if 'start search' in text:
                                search_button = button
                                print("Found search button by text content")
                                break
                except Exception as e:
                    print(f"Alternative approach failed: {e}")
            
            if not search_button:
                print("Start Search button not found")
                return False
            
            # Scroll to button to ensure it's visible
            print("Scrolling to Start Search button...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            self.human_like_delay(1, 2)
            
            # Try multiple click methods
            click_success = False
            
            # Method 1: Regular click
            try:
                print("Attempting regular click...")
                search_button.click()
                click_success = True
                print("Regular click successful!")
            except Exception as e:
                print(f"Regular click failed: {e}")
            
            # Method 2: JavaScript click
            if not click_success:
                try:
                    print("Attempting JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", search_button)
                    click_success = True
                    print("JavaScript click successful!")
                except Exception as e:
                    print(f"JavaScript click failed: {e}")
            
            # Method 3: ActionChains click
            if not click_success:
                try:
                    print("Attempting ActionChains click...")
                    actions = ActionChains(self.driver)
                    actions.move_to_element(search_button)
                    actions.pause(0.5)
                    actions.click()
                    actions.perform()
                    click_success = True
                    print("ActionChains click successful!")
                except Exception as e:
                    print(f"ActionChains click failed: {e}")
            
            if click_success:
                self.human_like_delay(2, 4)
                print("Search initiated!")
                return True
            else:
                print("All click methods failed")
                return False
            
        except Exception as e:
            print(f"Error clicking search button: {e}")
            return False
    
    def search_pimeyes(self, image_path):
        """Main search function with manual assistance"""
        try:
            print("Starting PimEyes search with manual assistance...")
            
            self.setup_driver()
            
            print("Navigating to PimEyes...")
            self.driver.get('https://pimeyes.com/en')
            
            self.handle_cookie_consent()
            
            if not self.upload_image_manual(image_path):
                print("Failed to upload image")
                return
            
            if not self.wait_for_challenge():
                print("Failed to detect challenge")
                return
            
            # Manual verification step
            if not self.manual_verification():
                print("Manual verification failed")
                return
            
            # Handle terms and conditions checkboxes
            if not self.handle_terms_checkboxes():
                print("Failed to handle terms checkboxes")
                return
            
            if not self.click_start_search():
                print("Failed to start search")
                return
            
            print("Search completed successfully!")
            print("Results should now be loading...")
            
        except Exception as e:
            print(f"Error during search: {e}")
        finally:
            input("Press Enter to close browser...")
            if self.driver:
                self.driver.quit()

def main():
    if len(sys.argv) < 2:
        print("Usage: python pimeyes_manual_assist.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' does not exist.")
        sys.exit(1)
    
    bypass = PimEyesManualAssist()
    bypass.search_pimeyes(image_path)

if __name__ == '__main__':
    main() 
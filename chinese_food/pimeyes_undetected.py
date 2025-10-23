import sys
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pathlib import Path
import os

class PimEyesUndetected:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup undetected Chrome driver"""
        try:
            print("Setting up undetected Chrome driver...")
            
            # Use undetected-chromedriver with minimal options
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            # Launch with undetected-chromedriver
            self.driver = uc.Chrome(options=options)
            
            print("Undetected driver setup successful")
            
        except Exception as e:
            print(f"Failed to setup undetected driver: {e}")
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
    
    def upload_image_manual(self, image_path):
        """Upload image with manual assistance"""
        try:
            print("Looking for upload area...")
            self.human_like_delay(2, 4)
            
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
                print("Waiting for image processing...")
                self.human_like_delay(5, 8)
                
                return True
            else:
                print("File input not found after clicking upload area")
                return False
                
        except Exception as e:
            print(f"Upload failed: {e}")
            return False
    
    def wait_for_captcha_or_success(self):
        """Wait for either captcha or success indicators"""
        try:
            print("Waiting for captcha or success indicators...")
            
            max_wait = 45  # Increased wait time
            start_time = time.time()
            error_detected = False
            
            while time.time() - start_time < max_wait:
                try:
                    # Check for error messages but completely ignore them - website shows temporary errors
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-v-c2310dd8].snack.error')
                    for element in error_elements:
                        if element.is_displayed():
                            if not error_detected:
                                print("Website showing error message - ignoring and continuing to wait...")
                                error_detected = True
                            # Don't return error - just continue waiting
                    
                    # Check for Turnstile/captcha indicators
                    captcha_indicators = [
                        '#turnstile-wrapper',
                        '#turnstile-captcha',
                        'iframe[src*="challenges.cloudflare.com"]',
                        'div[id^="cf-"]',
                        '.cf-turnstile',
                        '[class*="turnstile"]',
                        '[class*="captcha"]'
                    ]
                    
                    for selector in captcha_indicators:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed():
                                    print(f"Found captcha indicator: {selector}")
                                    return "captcha"
                        except:
                            continue
                    
                    # Check for success indicators
                    success_indicators = [
                        'input[data-v-dc978e0d][type="checkbox"]',
                        'button[data-v-6f435614]',
                        'div[data-v-c2310dd8].snack.success'
                    ]
                    
                    for selector in success_indicators:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed():
                                    print("Found success indicator - past captcha")
                                    return "success"
                        except:
                            continue
                    
                    time.sleep(1)
                
                except Exception as e:
                    print(f"Error checking status: {e}")
                    time.sleep(1)
            
            print("Timeout waiting for status - continuing anyway")
            return "timeout"
            
        except Exception as e:
            print(f"Error waiting for status: {e}")
            return "timeout"
    
    def manual_captcha_verification(self):
        """Handle manual captcha verification"""
        print("\n" + "="*60)
        print("MANUAL CAPTCHA VERIFICATION REQUIRED")
        print("="*60)
        print("1. Look for any captcha or verification checkbox")
        print("2. Complete the verification manually")
        print("3. Wait for verification to complete")
        print("4. Script will continue automatically")
        print("="*60)
        
        # Wait for user to complete verification
        # input("Press Enter after completing the captcha verification...")
        
        # Check if verification was successful
        success_indicators = [
            'input[data-v-dc978e0d][type="checkbox"]',
            'button[data-v-6f435614]',
            'div[data-v-c2310dd8].snack.success'
        ]
        
        for selector in success_indicators:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        print("Captcha verification successful!")
                        return True
            except:
                continue
        
        print("Captcha verification status unclear, continuing...")
        return True
    
    def handle_terms_checkboxes(self):
        """Handle the 3 required terms checkboxes"""
        try:
            print("Looking for terms and conditions checkboxes...")
            
            # Wait longer for checkboxes to appear after captcha resolution
            print("Waiting for checkboxes to appear after captcha...")
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    temp_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[data-v-dc978e0d][type="checkbox"]')
                    if len(temp_checkboxes) >= 3:
                        print(f"Found {len(temp_checkboxes)} checkboxes!")
                        break
                    else:
                        print(f"Found only {len(temp_checkboxes)} checkboxes, waiting...")
                        time.sleep(2)
                except:
                    time.sleep(2)
            
            # Find all required checkboxes
            checkbox_selectors = [
                'input[data-v-dc978e0d][type="checkbox"][required]',
                'input[data-v-dc978e0d][type="checkbox"]',
                'input[type="checkbox"][required]'
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
    
    def handle_prosopo_captcha(self):
        """Handle Prosopo 'I am human' captcha checkbox with ActionChains"""
        try:
            print("Looking for Prosopo 'I am human' captcha...")
            
            # Wait for the captcha to appear after terms checkboxes
            self.human_like_delay(3, 5)
            
            # First try to find the captcha container
            captcha_container = None
            try:
                captcha_container = self.driver.find_element(By.CSS_SELECTOR, '#captcha-container')
                print("Found captcha container")
            except:
                try:
                    captcha_container = self.driver.find_element(By.CSS_SELECTOR, '.prosopo-captcha-container')
                    print("Found prosopo captcha container")
                except:
                    pass
            
            if not captcha_container:
                print("Prosopo captcha container not found - may not be required")
                return True
            
            print("Prosopo captcha found, attempting to click 'I am human' checkbox...")
            
            # Scroll to captcha container
            self.driver.execute_script("arguments[0].scrollIntoView(true);", captcha_container)
            self.human_like_delay(1, 2)
            
            # Add human-like delay before clicking
            self.human_like_delay(2, 3)
            
            # Method 1: Try ActionChains click on container
            try:
                print("Trying ActionChains click on captcha container...")
                actions = ActionChains(self.driver)
                actions.move_to_element(captcha_container)
                actions.pause(0.5)
                actions.click()
                actions.perform()
                
                self.human_like_delay(1, 2)
                
                # Check if it worked
                verify_script = """
                const captchaContainer = document.querySelector('#captcha-container');
                if (captchaContainer) {
                    const prosopoElement = captchaContainer.querySelector('prosopo-procaptcha');
                    if (prosopoElement && prosopoElement.shadowRoot) {
                        const checkbox = prosopoElement.shadowRoot.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            return checkbox.checked;
                        }
                    }
                }
                return false;
                """
                
                result = self.driver.execute_script(verify_script)
                if result:
                    print("ActionChains click on container worked!")
                    self.human_like_delay(3, 5)
                    return True
                else:
                    print("ActionChains click on container did not work")
                    
            except Exception as e:
                print(f"ActionChains click failed: {e}")
            
            # Method 2: Try clicking at specific coordinates within the container
            try:
                print("Trying coordinate-based click...")
                
                # Get container location and size
                location = captcha_container.location
                size = captcha_container.size
                
                # Calculate center of container
                center_x = location['x'] + size['width'] // 2
                center_y = location['y'] + size['height'] // 2
                
                # Click at center of container
                actions = ActionChains(self.driver)
                actions.move_by_offset(center_x, center_y)
                actions.click()
                actions.perform()
                
                self.human_like_delay(1, 2)
                
                # Check if it worked
                verify_script = """
                const captchaContainer = document.querySelector('#captcha-container');
                if (captchaContainer) {
                    const prosopoElement = captchaContainer.querySelector('prosopo-procaptcha');
                    if (prosopoElement && prosopoElement.shadowRoot) {
                        const checkbox = prosopoElement.shadowRoot.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            return checkbox.checked;
                        }
                    }
                }
                return false;
                """
                
                result = self.driver.execute_script(verify_script)
                if result:
                    print("Coordinate-based click worked!")
                    self.human_like_delay(3, 5)
                    return True
                else:
                    print("Coordinate-based click did not work")
                    
            except Exception as e:
                print(f"Coordinate click failed: {e}")
            
            # Method 3: Try JavaScript click with different approach
            try:
                print("Trying JavaScript click with different approach...")
                
                # Try clicking the label instead of checkbox
                label_click_script = """
                const captchaContainer = document.querySelector('#captcha-container');
                if (captchaContainer) {
                    const prosopoElement = captchaContainer.querySelector('prosopo-procaptcha');
                    if (prosopoElement && prosopoElement.shadowRoot) {
                        const label = prosopoElement.shadowRoot.querySelector('label');
                        if (label) {
                            label.click();
                            return true;
                        }
                    }
                }
                return false;
                """
                
                result = self.driver.execute_script(label_click_script)
                if result:
                    print("Label click worked!")
                    self.human_like_delay(1, 2)
                    
                    # Verify checkbox is checked
                    verify_script = """
                    const captchaContainer = document.querySelector('#captcha-container');
                    if (captchaContainer) {
                        const prosopoElement = captchaContainer.querySelector('prosopo-procaptcha');
                        if (prosopoElement && prosopoElement.shadowRoot) {
                            const checkbox = prosopoElement.shadowRoot.querySelector('input[type="checkbox"]');
                            if (checkbox) {
                                return checkbox.checked;
                            }
                        }
                    }
                    return false;
                    """
                    
                    verify_result = self.driver.execute_script(verify_script)
                    if verify_result:
                        print("Label click verified successfully!")
                        self.human_like_delay(3, 5)
                        return True
                    else:
                        print("Label click verification failed")
                else:
                    print("Label click failed")
                    
            except Exception as e:
                print(f"Label click failed: {e}")
            
            # Method 4: Try simulating mouse events
            try:
                print("Trying mouse event simulation...")
                
                mouse_event_script = """
                const captchaContainer = document.querySelector('#captcha-container');
                if (captchaContainer) {
                    const prosopoElement = captchaContainer.querySelector('prosopo-procaptcha');
                    if (prosopoElement && prosopoElement.shadowRoot) {
                        const checkbox = prosopoElement.shadowRoot.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            // Simulate mouse down and up events
                            const mouseDownEvent = new MouseEvent('mousedown', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                button: 0
                            });
                            const mouseUpEvent = new MouseEvent('mouseup', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                button: 0
                            });
                            const clickEvent = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                button: 0
                            });
                            
                            checkbox.dispatchEvent(mouseDownEvent);
                            checkbox.dispatchEvent(mouseUpEvent);
                            checkbox.dispatchEvent(clickEvent);
                            
                            return checkbox.checked;
                        }
                    }
                }
                return false;
                """
                
                result = self.driver.execute_script(mouse_event_script)
                if result:
                    print("Mouse event simulation worked!")
                    self.human_like_delay(3, 5)
                    return True
                else:
                    print("Mouse event simulation did not work")
                    
            except Exception as e:
                print(f"Mouse event simulation failed: {e}")
            
            print("All automation methods failed - captcha may require manual interaction")
            return False
            
        except Exception as e:
            print(f"Error handling Prosopo captcha: {e}")
            return False
    
    def click_start_search(self):
        """Click the Start Search button (wait for it to be enabled)"""
        try:
            print("Looking for Start Search button...")
            
            # Wait for button to appear and become enabled
            max_wait = 15
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # Look for Start Search button
                    search_button = None
                    
                    try:
                        search_button = self.driver.find_element(By.XPATH, "//button[contains(span, 'Start Search')]")
                        print("Found search button using XPath")
                    except:
                        try:
                            search_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-v-04fe1977]')
                            print("Found search button by data attribute")
                        except:
                            pass
                    
                    if search_button:
                        # Check if button is enabled
                        is_enabled = search_button.is_enabled()
                        is_disabled = search_button.get_attribute("disabled")
                        
                        print(f"Button found - enabled: {is_enabled}, disabled attr: {is_disabled}")
                        
                        if is_enabled and not is_disabled:
                            print("Start Search button is enabled, clicking...")
                            
                            # Scroll to button
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                            self.human_like_delay(1, 2)
                            
                            # Click the button
                            try:
                                search_button.click()
                                print("Search button clicked successfully!")
                                self.human_like_delay(2, 4)
                                return True
                            except Exception as e:
                                print(f"Click failed: {e}")
                                return False
                        else:
                            print("Button is still disabled, waiting...")
                            time.sleep(1)
                    else:
                        print("Start Search button not found yet, waiting...")
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"Error checking button status: {e}")
                    time.sleep(1)
            
            print("Timeout waiting for Start Search button to become enabled")
            return False
            
        except Exception as e:
            print(f"Error clicking search button: {e}")
            return False
    
    def search_pimeyes(self, image_path):
        """Main search function"""
        try:
            print("Starting PimEyes search with undetected Chrome...")
            
            self.setup_driver()
            
            print("Navigating to PimEyes...")
            self.driver.get('https://pimeyes.com/en')
            
            self.handle_cookie_consent()
            
            if not self.upload_image_manual(image_path):
                print("Failed to upload image")
                return
            
            # Wait for captcha or success
            status = self.wait_for_captcha_or_success()
            
            # Always continue regardless of status - captcha may resolve itself
            if status == "success":
                print("Already past captcha - continuing...")
            else:
                print("Continuing to terms checkboxes...")
            
            # Handle terms and conditions checkboxes
            if not self.handle_terms_checkboxes():
                print("Failed to handle terms checkboxes")
                return
            
            # Handle Prosopo 'I am human' captcha
            if not self.handle_prosopo_captcha():
                print("Failed to handle Prosopo captcha")
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
        print("Usage: python pimeyes_undetected.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' does not exist.")
        sys.exit(1)
    
    # Check if undetected-chromedriver is installed
    try:
        import undetected_chromedriver
    except ImportError:
        print("Error: undetected-chromedriver is not installed.")
        print("Install it with: pip install undetected-chromedriver")
        sys.exit(1)
    
    bypass = PimEyesUndetected()
    bypass.search_pimeyes(image_path)

if __name__ == '__main__':
    main()

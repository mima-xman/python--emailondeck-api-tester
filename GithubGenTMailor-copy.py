import random
import string
import json
import time
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError
from TMailorAPI import TMailorAPI
from config import (
    FIRST_NAMES,
    LAST_NAMES,
    OUTPUT_DIR,
    HEADLESS,
    ARGS,
    VIEWPORT,
    LOCALE,
    USER_AGENT,
    BRAVE_PATH,
    CHROME_PATH
)
from utils import logger, format_error, renew_tor, get_current_ip
from dotenv import load_dotenv

load_dotenv()

# GitHub Specific Constants
GITHUB_SIGNUP_URL = "https://github.com/signup"
EMAIL_SELECTOR = "#email"
PASSWORD_SELECTOR = "#password"
USERNAME_SELECTOR = "#login"
SUBMIT_BUTTON_SELECTOR = "#signup-form > form > div:nth-child(7) > button"
USERNAME_PREFIX = "dev1"  # Added prefix

class GithubTMailorGenerator:
    """GitHub account generator using TMailor API."""
    
    def __init__(self, use_tor=False, tor_port=9150, tor_control_port=9151):
        self.use_tor = use_tor
        self.tor_port = int(os.getenv("TOR_PORT", tor_port))
        self.tor_control_port = int(os.getenv("TOR_CONTROL_PORT", tor_control_port))
        self.account_data = {}
        self.page = None
        self.browser = None
        self.context = None
        self.playwright = None
        self.screenshot_counter = 1
        
        # Log TOR ports
        logger(f"TOR Port: {self.tor_port}", level=1)
        logger(f"TOR Control Port: {self.tor_control_port}", level=1)
        
        # Create output directories
        current_date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.screenshots_dir = os.path.join(OUTPUT_DIR, f"github_screenshots_{current_date_time}")
        self.html_reports_dir = os.path.join(OUTPUT_DIR, f"github_html_reports_{current_date_time}")
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.html_reports_dir, exist_ok=True)

        if self.use_tor:
             logger("Using TOR network for emails...", level=1)
             renew_tor(self.tor_control_port, level=1)
             tor_proxies = {
                "http": f"socks5://127.0.0.1:{self.tor_port}",
                "https": f"socks5://127.0.0.1:{self.tor_port}"
             }
             get_current_ip(proxies=tor_proxies, level=1)

    def human_delay(self, min_ms=500, max_ms=1500):
        """Introduces a random human-like delay."""
        time.sleep(random.uniform(min_ms, max_ms) / 1000)

    def human_type(self, selector, text, min_delay_ms=50, max_delay_ms=200):
        """Simulates human typing with random delays between characters."""
        try:
             self.page.type(selector, text, delay=random.randint(min_delay_ms, max_delay_ms))
        except Exception as e:
             logger(f"⚠ Human type fallback for {selector}: {e}")
             self.page.fill(selector, text)

    def human_click(self, selector):
        """Simulates a human click with a small delay before the action."""
        try:
            self.page.hover(selector)
            self.human_delay(300, 700)
            self.page.click(selector)
            return True
        except Exception as e:
            logger(f"⚠ Human click failed, retrying force click: {e}")
            try:
                self.page.click(selector, force=True)
                return True
            except Exception as e2:
                 logger(f"✗ Click completely failed: {e2}")
                 return False

    def natural_delay(self, min_s=1, max_s=3):
        """Adds natural random pause between major actions."""
        time.sleep(random.uniform(min_s, max_s))

    def __generate_account_info(self, level: int = 0):
        """Generate random account information."""
        print("  ")
        logger("[######] Generating account info...", level=level)

        try:
            # Generate strong password
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(chars) for _ in range(15))

            # Generate name
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"

            # Generate username: {prefix}{firstname}{lastname} all lower
            username = f"{first_name}{last_name}-{USERNAME_PREFIX}".lower()
            
            self.account_data = {
                "email_address": None,
                "password": password,
                "username": username,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            logger(f"✓ Generated account info: {username} | {password}", level=level+1)
            return self.account_data
        except Exception as e:
            logger(f"✗ Failed to generate account info: {format_error(e)}", level=level+1)
            return None

    def __get_email_address(self, level: int = 0):
        """Get email address from TMailorAPI service."""
        print("  ")
        logger("[######] Getting email address...", level=level)

        try:
            self.email_service = TMailorAPI()
            # Pass level + 1 if the method accepts it, otherwise it might print directly
            result = self.email_service.generate_email(level=level+1)
        
            if not result or not result.get('email'):
                logger("✗ Failed to generate email address", level=level+1)
                return None
            
            email_address = result['email']
            self.account_data['email_address'] = email_address
            self.account_data['email_token'] = result.get('code', 'N/A')
        
            logger(f"✓ Email obtained: {email_address}", level=level+1)
            return email_address
        except Exception as e:
            logger(f"✗ Failed to get email address: {format_error(e)}", level=level+1)
            return None

    def __save_screenshot_and_page_html(self, level: int = 0):
        """Take a screenshot and save page HTML for debugging."""
        print("  ")
        logger("[######] Saving screenshot...", level=level)

        if self.page:
            try:
                screenshot_path = f"{self.screenshots_dir}/{self.screenshot_counter}.png"
                self.page.screenshot(path=screenshot_path)
                logger(f"✓ Screenshot saved: {screenshot_path}", level=level+1)
                self.screenshot_counter += 1
            except Exception as e:
                logger(f"✗ Screenshot failed: {format_error(e)}", level=level+1)
        else:
            logger("✗ No page to save screenshot", level=level+1)

    def __launch_browser(self, level: int = 0):
        """Launch browser."""
        print("  ")
        logger("[######] Launching browser...", level=level)
        
        try:
            launch_kwargs = {
                "headless": HEADLESS,
                "args": ARGS
            }

            if self.use_tor:
                # Default Tor Browser port is 9150, System Tor is 9050
                # Using 9150 to match EmailOnDeck default
                tor_proxy = f"socks5://127.0.0.1:{self.tor_port}"
                launch_kwargs["proxy"] = {"server": tor_proxy}
                logger(f"Using Tor proxy: {tor_proxy}", level=level+1)

            # Check for Browser
            BROWSER_PATH = CHROME_PATH
            if os.path.exists(BROWSER_PATH):
                launch_kwargs["executable_path"] = BROWSER_PATH
                logger(f"Using Browser: {BROWSER_PATH}", level=level+1)
            else:
                logger(f"⚠ Browser not found at {BROWSER_PATH}, using default Chromium", level=level+1)

            self.browser = self.playwright.chromium.launch(**launch_kwargs)
            
            self.context = self.browser.new_context(
                viewport=VIEWPORT,
                locale=LOCALE,
                user_agent=USER_AGENT
            )
            
            # Remove webdriver property
            self.context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            self.page = self.context.new_page()
            
            logger("✓ Browser launched successfully", level=level+1)
            return True
        except Exception as e:
            logger(f"✗ Error launching browser: {format_error(e)}", level=level+1)
            return False



    def __wait_and_fill(self, selector, value, field_name, level: int = 0):
        """Wait for field and fill it."""
        print("  ")
        logger(f"[######] Filling {field_name}...", level=level)
        
        try:
            self.page.wait_for_selector(selector, state='visible', timeout=30000)
            self.page.click(selector)
            self.human_type(selector, value)
            logger(f"✓ {field_name} filled", level=level+1)
            self.network_idle_wait()
            return True
        except Exception as e:
            logger(f"✗ Failed to fill {field_name}: {e}", level=level+1)
            self.__save_screenshot_and_page_html(level=level+1)
            return False

    def network_idle_wait(self):
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except:
            pass

    def run_flow(self, level: int = 0):
        """Execute the complete account creation flow."""
        print("  ")
        logger("GitHub TMailor Account Generator", level=level)
        
        with sync_playwright() as p:
            self.playwright = p
            
            try:
                # 1. Get Email
                current_email = self.__get_email_address(level=level+1)
                if not current_email:
                    return False

                # 2. Generate Credentials
                self.__generate_account_info(level=level+1)
                # Ensure email is in account data
                self.account_data['email_address'] = current_email

                # 3. Launch Browser
                if not self.__launch_browser(level=level+1):
                    return False

                # 4. Navigate to Signup
                print("  ")
                logger("[######] Opening GitHub signup...", level=level+1)
                self.page.goto(GITHUB_SIGNUP_URL, timeout=60000)
                self.network_idle_wait()


                # 0. Accept Cookies
                try:
                    button_accept_cookies_selector = "#wcpConsentBannerCtrl > div > button:nth-child(1)"
                    self.page.wait_for_selector(button_accept_cookies_selector, timeout=30000)
                    self.page.click(button_accept_cookies_selector)
                    logger("✓ Accepted cookies", level=level+2)
                except:
                    logger("✗ Failed to accept cookies", level=level+2)
                    pass

                # 5. Fill Fields
                # Email
                self.natural_delay()
                if not self.__wait_and_fill(EMAIL_SELECTOR, self.account_data['email_address'], "Email", level=level+1):
                    return False
                
                self.natural_delay()
                
                # Check if password field is visible
                if not self.page.is_visible(PASSWORD_SELECTOR):
                    logger("Password field not yet visible, creating 'Continue' action...", level=level+1)
                    self.page.press(EMAIL_SELECTOR, "Enter")
                
                if not self.__wait_and_fill(PASSWORD_SELECTOR, self.account_data['password'], "Password", level=level+1):
                    return False

                self.natural_delay()
                
                # Check if username field is visible
                if not self.page.is_visible(USERNAME_SELECTOR):
                    logger("Username field not yet visible, creating 'Continue' action...", level=level+1)
                    self.page.press(PASSWORD_SELECTOR, "Enter")

                if not self.__wait_and_fill(USERNAME_SELECTOR, self.account_data['username'], "Username", level=level+1):
                    return False

                self.natural_delay(5, 10)
                
                # 6. Click Submit
                print("  ")
                logger("[######] Clicking Submit...", level=level+1)
                
                if not self.page.is_visible(SUBMIT_BUTTON_SELECTOR):
                     self.page.press(USERNAME_SELECTOR, "Enter")

                self.page.wait_for_selector(SUBMIT_BUTTON_SELECTOR, state='visible', timeout=10000)
                
                self.natural_delay()

                self.human_click(SUBMIT_BUTTON_SELECTOR)
                logger("✓ Submit clicked", level=level+2)
                
                self.natural_delay(2, 5) # Wait for processing

                iframe1_exists = self.__check_iframe1_exists(level=level+1)
                if not iframe1_exists:
                    for _ in range(3):
                        iframe1_exists = self.__check_iframe1_exists(level=level+1)
                        if iframe1_exists:
                            break
                        self.natural_delay(2, 5)

                while iframe1_exists:
                    logger("iframe 1 still exists", level=level+2)
                    self.natural_delay(2, 5)
                    iframe1_exists = self.__check_iframe1_exists(level=level+1)

                # 7. Handle Captcha
                # self.__handle_captcha(level=level+1)

                # 7. check verification code field displayed
                verification_code_form_exists = self.__check_verification_code_form_exists(level=level+1)
                if not verification_code_form_exists:
                    for _ in range(3):
                        verification_code_form_exists = self.__check_verification_code_form_exists(level=level+1)
                        if verification_code_form_exists:
                            break
                        self.natural_delay(2, 5)

                # 8. get verification code from email
                # #launch-code-{input-number} | exists 7 inputs because the code recived in email like this XXXXXXX
                code = None
                new_email = self.email_service.wait_for_email(120)
                if new_email:
                    # Get email content
                    content = self.email_service.get_email(new_email['id'], new_email['email_id'], level=level+2)
                    if content:
                        code = re.search(r'\d{7}', content['body'])
                        logger(f"Verification code: {code}", level=level+2)
                
                if not code:
                    logger("Verification code not found", level=level+2)
                    return False

                # 9. fill verification code field
                # #launch-code-{input-number} | exists 7 inputs because the code recived in email like this XXXXXXX
                for i in range(7):
                    self.page.fill(f"#launch-code-{i}", code[i])
                    logger(f"Filled verification code field {i+1}: {str(code)[i]}", level=level+2)
                    self.natural_delay()

                # 10. click submit
                # body > div > div > div > main > div > div > div > react-partial > div > div > div:nth-child(1) > form > div:nth-child(4) > button
                submit_button_selector = "body > div > div > div > main > div > div > div > react-partial > div > div > div:nth-child(1) > form > div:nth-child(4) > button"
                self.page.wait_for_selector(submit_button_selector, state='visible', timeout=10000)
                self.page.click(submit_button_selector)
                logger("✓ Submit clicked", level=level+2)
                
                time.sleep(20)
                logger("✓ Waited for 20 seconds", level=level+2)

                self.__save_screenshot_and_page_html(level=level+1)

                logger("✓ Flow execution finished", level=level+1)
                
                # Wait for user input to close
                logger("Waiting for user input to close browser...", level=level+1)
                input("Press Enter to close the browser...")

                return True

            except Exception as e:
                logger(f"✗ An error occurred: {format_error(e)}", level=level+1)
                self.__save_screenshot_and_page_html(level=level+1)
                return False
            finally:
                if self.browser:
                    self.browser.close()


    def __check_iframe1_exists(self, level: int = 0):
        try:
            iframe1_selector = "#captcha-container-nux > div > div > div:nth-child(3) > iframe"
            self.page.wait_for_selector(iframe1_selector, state='attached', timeout=30000)
            logger("✓ Iframe 1 exists", level=level+2)
            return True
        except:
            logger("✗ Iframe 1 not found", level=level+2)
            return False
    


    def __check_verification_code_form_exists(self, level: int = 0):
        try:
            form_selector = "body > div > div > div > main > div > div > div > react-partial > div > div > div:nth-child(1) > form"
            self.page.wait_for_selector(form_selector, state='attached', timeout=30000)
            logger("✓ Verification code form exists", level=level+2)
            return True
        except:
            logger("✗ Verification code form not found", level=level+2)
            return False


    def __handle_captcha(self, level: int = 0):
        """Handle GitHub's funky nested captcha."""
        print("  ")
        logger("[######] Handling Captcha...", level=level)

        try:
            from BytezSolver import BytezSolver
            if not hasattr(self, 'solver'):
                self.solver = BytezSolver(level=level)

            # 7. Wait for Iframe 1
            iframe1_selector = "#captcha-container-nux > div > div > div:nth-child(3) > iframe"
            
            logger(f"Waiting for iframe1: {iframe1_selector[:30]}...", level=level+1)
            try:
                self.page.wait_for_selector(iframe1_selector, state='attached', timeout=30000)
            except TimeoutError:
                logger("⚠ Specific iframe1 selector failed, trying generic...", level=level+1)
                iframe1_selector = "#captcha-container-nux iframe"
                self.page.wait_for_selector(iframe1_selector, state='attached', timeout=30000)

            iframe1 = self.page.frame_locator(iframe1_selector)
            
            # Check loading text
            logger("Checking for loading text...", level=level+1)
            try:
                iframe1.locator("#text-loading").wait_for(state='visible', timeout=10000)
                logger("✓ Loading text displayed", level=level+1)
            except TimeoutError:
                logger("⚠ Loading text not found (might have loaded already)", level=level+1)
            
            # 8. Wait for Iframe 2
            iframe2_selector = "#funcaptcha > div > iframe"
            logger(f"Waiting for iframe2: {iframe2_selector}...", level=level+1)
            iframe1.locator(iframe2_selector).wait_for(state='attached', timeout=30000)
            iframe2 = iframe1.frame_locator(iframe2_selector)
            
            # 9. Wait for Iframe 3
            iframe3_selector = "#game-core-frame"
            logger(f"Waiting for iframe3: {iframe3_selector}...", level=level+1)
            iframe2.locator(iframe3_selector).wait_for(state='attached', timeout=30000)
            iframe3 = iframe2.frame_locator(iframe3_selector)
            
            # Button "Visual puzzle"
            puzzle_btn_selector = "#root > div > div > button[aria-label='Visual puzzle']"

            # It might auto-start or require clicking "Visual puzzle"
            # We check if button exists; if not, maybe it's already on the puzzle
            if iframe3.locator(puzzle_btn_selector).is_visible(timeout=5000):
                logger("Waiting for 'Visual puzzle' button...", level=level+1)
                iframe3.locator(puzzle_btn_selector).click()
                logger("✓ 'Visual puzzle' button clicked", level=level+1)
                self.natural_delay()

            # Captcha Loop
            # We don't know how many rounds, so we loop until success or timeout/limit
            max_rounds = 10
            for round_idx in range(max_rounds):
                logger(f"--- Captcha Round {round_idx + 1} ---", level=level+1)
                
                # Check if we are done (e.g. check status or if puzzle gone)
                # For now, we assume if question selector is gone/hidden, we might be done?
                # Or look for "Verification complete" text?
                
                # 10. Wait for question and image
                question_selector = "#root > div > div > div > h2 > span" 
                
                try:
                     iframe3.locator(question_selector).wait_for(state='visible', timeout=10000)
                except:
                     logger("⚠ Question not found, maybe captcha is done?", level=level+1)
                     break
                     
                question_text = iframe3.locator(question_selector).text_content()
                logger(f"→ Question: {question_text}", level=level+2)
                
                image_selector = "#root > div > div > div > div > div > div > img"
                iframe3.locator(image_selector).wait_for(state='visible', timeout=10000)
                image_element = iframe3.locator(image_selector)
                
                image_url = image_element.evaluate("el => el.style.backgroundImage")
                if image_url:
                    match = re.search(r'url\("(.*?)"\)', image_url)
                    if match:
                        image_url = match.group(1)
                
                if not image_url or image_url == 'none':
                     image_url = image_element.get_attribute("src")
                
                logger(f"→ Image URL: {image_url}", level=level+2)
                
                # 11. Download the image
                if image_url:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"captcha_{timestamp}.png"
                    filepath = os.path.join(self.screenshots_dir, filename)
                    
                    logger("Opening new page for full image download...", level=level+2)
                    image_page = self.context.new_page()
                    # image_page.set_viewport_size({"width": 1366, "height": 768})
                    
                    try:
                        image_page.goto(image_url)
                        time.sleep(1) 
                        image_page.screenshot(path=filepath)
                        logger(f"✓ Full Image downloaded: {filepath}", level=level+2)
                    except Exception as nav_e:
                        logger(f"✗ Failed to navigate/capture in new page: {nav_e}", level=level+2)
                        filepath = None # Mark as failed
                    finally:
                        image_page.close()
                    
                    if filepath:
                        # 12. Solve Puzzle
                        answer_idx = self.solver.solve_puzzle(filepath, question_text, level=level+2)
                        
                        if answer_idx is not None:
                            logger(f"✓ AI Answer: Option {answer_idx}", level=level+2)
                            
                            clicks_needed = answer_idx - 1
                            if clicks_needed > 0:
                                next_arrow = "#root > div > div > div > div > div > div > a.right-arrow"
                                for i in range(clicks_needed):
                                    logger(f"  → Clicking next arrow ({i+1}/{clicks_needed})", level=level+3)
                                    
                                    # Human-like click with random offset and delay
                                    arrow_btn = iframe3.locator(next_arrow)
                                    
                                    # Random delay before click
                                    time.sleep(random.uniform(0.8, 1.5))
                                    
                                    try:
                                        # Get bounding box to click randomly inside
                                        box = arrow_btn.bounding_box()
                                        if box:
                                            x_offset = random.uniform(5, box['width'] - 5)
                                            y_offset = random.uniform(5, box['height'] - 5)
                                            arrow_btn.click(position={"x": x_offset, "y": y_offset})
                                        else:
                                            arrow_btn.click()
                                    except Exception:
                                        arrow_btn.click()
                                        
                            else:
                                logger("  → Option 1 selected (0 clicks)", level=level+3)
                                
                            self.natural_delay(1, 2)
                            
                            # Click Submit/Done
                            try:
                                buttons_selector = "#root > div > div > div > button"
                                submit_button = iframe3.locator(buttons_selector).filter(has_text="Submit")
                                if submit_button.is_visible(timeout=2000):
                                    # Human-like click for submit
                                    time.sleep(random.uniform(0.5, 1.0))
                                    try:
                                        box = submit_button.bounding_box()
                                        if box:
                                            x_offset = random.uniform(5, box['width'] - 5)
                                            y_offset = random.uniform(5, box['height'] - 5)
                                            submit_button.click(position={"x": x_offset, "y": y_offset})
                                        else:
                                            submit_button.click()
                                    except:
                                        submit_button.click()
                                        
                                    logger("✓ Puzzle Submit button clicked", level=level+2)
                                    self.natural_delay(2, 4)
                                else:
                                    logger("✗ Submit button not found", level=level+2)
                            except:
                                pass # Maybe it auto-submits?
                        else:
                            logger("✗ AI failed to solve, stopping loop logic for safety", level=level+2)
                            break
            
            return True

        except Exception as e:
            logger(f"✗ Captcha handling failed: {format_error(e)}", level=level+1)
            return False
    

    def run_flow_with_retries(self, max_retries: int = 3, level: int = 0):
        print("  ")
        logger("Running flow with retries...", level=level)

        try:
            for i in range(max_retries):
                try:
                    if self.run_flow(level=level+1):
                        return True
                    
                    logger(f"✗ Run flow failed, retrying ({i+1}/{max_retries})", level=level+1)
                    renew_tor(self.tor_control_port, level=level+1)
                    time.sleep(random.uniform(5, 10))
                except Exception as e:
                    logger(f"✗ Run flow failed, retrying ({i+1}/{max_retries}): {format_error(e)}", level=level+1)
                    renew_tor(self.tor_control_port, level=level+1)
                    time.sleep(random.uniform(5, 10))
            return False
        except Exception as e:
            logger(f"✗ Run flow failed: {format_error(e)}", level=level+1)
            return False




if __name__ == "__main__":
    # Enable Tor by default as requested
    generator = GithubTMailorGenerator(use_tor=True)
    generator.run_flow_with_retries()

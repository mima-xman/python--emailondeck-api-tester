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
    USERNAME_SUFFIX,
    ERROR_MESSAGE_SELECTOR,
    NEXT_BUTTON_SELECTOR,
    EMAIL_FIELD_SELECTOR,
    VERIFICATION_CODE_SELECTOR,
    DIDNT_RECEIVE_CODE_BUTTON_SELECTOR,
    CHANGE_EMAIL_BUTTON_SELECTOR,
    MAX_WAIT_TIME_FOR_VERIFICATION_CODE,
    MAX_RETRIES_FOR_ACCOUNT_CREATION,
    VIEWPORT,
    LOCALE,
    USER_AGENT,
    HEADLESS,
    ARGS,
    MAX_LOAD_ATTEMPTS_FOR_OPENING_INSTAGRAM_SIGNUP,
    NAME_SELECTOR,
    PASSWORD_SELECTOR,
    BIRTHDATE_SELECTOR,
    USERNAME_SELECTOR,
    ACCEPT_BUTTON_SELECTOR,
    OUTPUT_DIR,
    INSTAGRAM_ACCOUNTS_INFO_FILENAME,
    INSTAGRAM_SIGNUP_URL,
    MAX_RETRIES_FOR_ACCOUNT_STATUS_CHECK,
    CHROME_PATH
)
from utils import logger, format_error



class InstagramMobileGenerator:
    """Simple and clean Instagram account generator for mobile version."""
    
    def __init__(self, use_tor=False):
        self.use_tor = use_tor
        self.account_data = {}
        self.page = None
        self.browser = None
        self.context = None
        self.playwright = None
        self.screenshot_and_html_counter = 1
        
        # Create screenshots and html reports directories
        current_date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.screenshots_dir = os.path.join(OUTPUT_DIR, f"screenshots_{current_date_time}")
        self.html_reports_dir = os.path.join(OUTPUT_DIR, f"html_reports_{current_date_time}")

        if self.use_tor:
             logger("Using TOR network for emails...", level=level+1)

        # Create screenshots and html reports directories
        current_date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.screenshots_dir = os.path.join(OUTPUT_DIR, f"screenshots_{current_date_time}")
        self.html_reports_dir = os.path.join(OUTPUT_DIR, f"html_reports_{current_date_time}")

        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.html_reports_dir, exist_ok=True)


    def human_delay(self, min_ms=500, max_ms=1500):
        """Introduces a random human-like delay."""
        time.sleep(random.uniform(min_ms, max_ms) / 1000)

    def human_type(self, selector, text, min_delay_ms=50, max_delay_ms=200):
        """Simulates human typing with random delays between characters."""
        try:
             self.page.type(selector, text, delay=random.randint(min_delay_ms, max_delay_ms))
        except Exception as e:
            # Fallback if standard type fails/times out
             logger(f"⚠ Human type fallback for {selector}: {e}")
             self.page.fill(selector, text)

    def human_click(self, selector):
        """Simulates a human click with a small delay before the action."""
        try:
            # Randomly move mouse before clicking (if supported) to simulate attention
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
            password = ''.join(random.choice(chars) for _ in range(12))

            # Generate name
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"

            # Generate username
            username_base = f"{first_name}{last_name}".lower()
            username = f"{username_base}.{USERNAME_SUFFIX}"

            # Generate birthdate (before 1999)
            year = random.randint(1980, 1998)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            
            # Format date for mobile input (DDMMYYYY for masked input)
            birthdate_str = f"{day:02d}{month:02d}{year}"

            self.account_data = {
                "email_address": None,
                "email_token": None,
                "password": password,
                "complete_name": full_name,
                "profile_name": username,
                "birth_date": birthdate_str,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            logger(f"✓ Generated account info for: {full_name}", level=level+1)
            return self.account_data
        except Exception as e:
            logger(f"✗ Failed to generate account info: {format_error(e)}", level=level+1)
            return None


    def __get_email_address(self, level: int = 0):
        """Get email address from EmailOnDeck service."""
        print("  ")
        logger("[######] Getting email address...", level=level)

        try:
            self.email_service = TMailorAPI()
            email_data = self.email_service.generate_email(level=level+1)
            email_address = email_data.get('email', None)
            email_token = email_data.get('token', None)
        
            if not email_address:
                logger("✗ Failed to generate email address", level=level+1)
                return None
        
            self.account_data['email_address'] = email_address
            self.account_data['email_token'] = email_token
        
            logger(f"✓ Email obtained: {email_address}", level=level+1)
            return email_address
        except Exception as e:
            logger(f"✗ Failed to get email address: {format_error(e)}", level=level+1)
            return None


    def __wait_for_element(self, selector, name=None, timeout=30000, save_screenshot_and_html_on_failed=True, level: int = 0):
        """Wait for element to be visible."""
        print("  ")
        logger("[######] Waiting for element...", level=level)

        try:
            self.page.wait_for_selector(selector, state='visible', timeout=timeout)
            
            logger(f"✓ Element found: {name if name else selector[:20]+'...'}", level=level+1)
            return True
        except TimeoutError as e:
            logger(f"✗ Timeout waiting for element: {name if name else selector[:20]+'...'}: {format_error(e)}", level=level+1)
            if save_screenshot_and_html_on_failed:
                self.__save_screenshot_and_page_html(level=level+1)
            return False
        except Exception as e:
            logger(f"✗ Failed to wait for element: {name if name else selector[:20]+'...'}: {format_error(e)}", level=level+1)
            if save_screenshot_and_html_on_failed:
                self.__save_screenshot_and_page_html(level=level+1)
            return False


    def __click_button_with_dispatch(self, selector, name=None, save_screenshot_and_html_on_failed=True, level: int = 0):
        """Click button using Human-like interaction."""
        print("  ")
        logger("[######] Clicking button (Human)...", level=level)

        if not self.__wait_for_element(selector, name=name, save_screenshot_and_html_on_failed=save_screenshot_and_html_on_failed, level=level+1):
            return False

        self.human_delay(500, 1000)
        
        logger(f"→ Clicking button: {name if name else selector[:20]+'...'}", level=level+1)
        
        clicked = self.human_click(selector)
        
        if clicked:
            logger("✓ Button clicked", level=level+1)
            self.natural_delay(1, 2)
            return True
        else:
            logger("✗ Failed to click button", level=level+1)
            if save_screenshot_and_html_on_failed:
                self.__save_screenshot_and_page_html(level=level+1)
            return False
    

    def __fill_field(self, selector, value, name=None, save_screenshot_and_html_on_failed=True, log_value=True, level: int = 0):
        """Fill field with text using human-like typing."""
        print("  ")
        logger("[######] Filling field (Human)...", level=level)
        
        try:
            if not self.__wait_for_element(selector, name=name, save_screenshot_and_html_on_failed=save_screenshot_and_html_on_failed, level=level+1):
                return False

            self.human_delay(500, 1000)

            # Focus the element first
            self.page.click(selector)
            self.human_delay(200, 500)
            
            # Clear existing content if needed
            self.page.fill(selector, "")

            self.human_type(selector, value)
            
            self.natural_delay(0.5, 1.5)
            
            logger(f"✓ {name if name else selector[:20]+'...'} filled: {value if log_value else '*' * 5}", level=level+1)
            self.__save_screenshot_and_page_html(level=level+1)
            return True
        except Exception as e:
            logger(f"✗ Failed to fill {name if name else selector[:20]+'...'}: {format_error(e)}", level=level+1)
            if save_screenshot_and_html_on_failed:
                self.__save_screenshot_and_page_html(level=level+1)
            return False


    def __check_for_error_message(self, level: int = 0):
        """Check if an error message is displayed on the page."""
        print("  ")
        logger("[######] Checking for error message...", level=level)

        try:
            if self.__wait_for_element(ERROR_MESSAGE_SELECTOR, name="Error Message", save_screenshot_and_html_on_failed=False, level=level+1):
                error_message = self.page.text_content(ERROR_MESSAGE_SELECTOR)
                if error_message:
                    error_message_text = error_message.strip()
                    logger(f"→ Error Detected: {error_message_text}", level=level+1)
                    self.__save_screenshot_and_page_html(level=level+1)
                    return error_message_text
            
            logger("→ No error message detected", level=level+1)
            return None
        except Exception as e:
            logger(f"✗ Error checking for error message: {format_error(e)}", level=level+1)
            self.__save_screenshot_and_page_html(level=level+1)
            return None

    
    def __save_screenshot_and_page_html(self, level: int = 0):
        """Take a screenshot and save page HTML for debugging."""
        print("  ")
        logger("[######] Saving screenshot and page HTML...", level=level)

        if self.page:
            
            try:
                # Take screenshot
                screenshot_path = f"{self.screenshots_dir}/{self.screenshot_and_html_counter}.png"
                self.page.screenshot(path=screenshot_path)
                logger(f"✓ Screenshot saved  : {screenshot_path}", level=level+1)
            except Exception as e:
                logger(f"✗ Screenshot failed : {format_error(e)}", level=level+1)
                
            try:
                # Save page HTML
                html_path = f"{self.html_reports_dir}/{self.screenshot_and_html_counter}.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                logger(f"✓ HTML saved        : {html_path}", level=level+1)
            except Exception as e:
                logger(f"✗ HTML save failed  : {format_error(e)}", level=level+1)

            # Increment screenshots counter
            self.screenshot_and_html_counter += 1
        else:
            logger("✗ No page to save screenshot and HTML", level=level+1)
    

    def __wait_for_verification_code(self, level: int = 0):
        """Wait for verification code to be visible."""
        print("  ")
        logger("[######] Waiting for verification code...", level=level)
        
        code = None
        start_time = time.time()
        
        while time.time() - start_time < MAX_WAIT_TIME_FOR_VERIFICATION_CODE:
            inbox = self.email_service.get_inbox(level=level+1)
            messages = inbox.get('emails', [])
            
            if messages:
                msg = messages[0]
                logger(f"message: {msg}", level=level+1)
                logger(f"✓ Email received: {msg.get('subject')}", level=level+1)
                
                # Try to extract code from subject
                match = re.search(r'\b\d{6}\b', msg.get('subject'))
                if match:
                    code = match.group(0)
                else:
                    # Try to extract from content
                    msg_data = self.email_service.get_email(msg.get('id'), msg.get('email_id'), level=level+1)
                    content = msg_data.get('body', '')
                    match = re.search(r'\b\d{6}\b', str(content))
                    if match:
                        code = match.group(0)
                
                if code:
                    logger(f"✓ Verification code found: {code}", level=level+1)
                    break
            else:
                logger("✗ No message received", level=level+1)
            
            time.sleep(5)
        
        if not code:
            logger("✗ No verification code received", level=level+1)
            return None
        
        return code
    

    def __click_change_email_button_for_retry_with_new_email(self, level: int = 0):
        """Click on the 'Change email' button for retry with a new email address from step 2"""
        print("  ")
        logger("[middle step] Clicking 'Change email' button...", level=level)

        # Find the button with text "Je n'ai pas reçu le code"
        if not self.__click_button_with_dispatch(DIDNT_RECEIVE_CODE_BUTTON_SELECTOR, name="Je n'ai pas reçu le code", level=level+1):
            return False
        
        if not self.__click_button_with_dispatch(CHANGE_EMAIL_BUTTON_SELECTOR, name="Changer adresse e-mail", level=level+1):
            return False
        
        time.sleep(2)
            
        return True
    

    def __save_account_to_json(self, filename=INSTAGRAM_ACCOUNTS_INFO_FILENAME, level: int = 0):
        """Save account data to JSON file."""
        print("  ")
        logger("[######] Saving account data...", level=level)

        try:
            path = f"{OUTPUT_DIR}/{filename}"
            logger(f"✓ Path: {path}", level=level+1)
            
            if os.path.exists(path):
                with open(path, 'r') as f:
                    try:
                        data = json.load(f)
                        logger(f"✓ {len(data)} accounts found", level=level+1)
                    except json.JSONDecodeError as e:
                        data = []
                        logger(f"✗ Failed to load account data: {format_error(e)}", level=level+1)
            else:
                data = []
                logger(f"✓ No account data found", level=level+1)
            
            if not isinstance(data, list):
                data = [data]
            
            data.append(self.account_data)
            logger(f"✓ New account data appended", level=level+1)
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
                logger(f"✓ Account file updated", level=level+1)
                
        except Exception as e:
            logger(f"✗ Error saving account: {format_error(e)}", level=level)
    

    def __check_account_status(self, max_retries: int = MAX_RETRIES_FOR_ACCOUNT_STATUS_CHECK, level: int = 0):
        """Check if account was created successfully or suspended."""
        print("  ")
        logger("[######] Verifying account status...", level=level)
        
        current_url = ""
        for i in range(max_retries):
            try:
                # Force get current URL from page execution context to avoid stale state
                current_url = self.page.evaluate("window.location.href")
                logger(f"✓ Current URL (try {i+1}/{max_retries}): {current_url}", level=level+1)
                
                # Check for explicit states first
                if "suspended" in current_url.lower():
                    logger("✗ Account suspended detected immediately", level=level+1)
                    break
                    
                if "challenge" in current_url.lower():
                    logger("⚠ Account challenged detected", level=level+1)
                    break

                # If we are no longer on the signup page (and not just because of a hash change)
                # We strip the hash to be sure we really moved away
                base_signup = INSTAGRAM_SIGNUP_URL.split("#")[0]
                if base_signup not in current_url.split("#")[0]:
                    logger("✓ Signup page changed", level=level+1)
                    break
                
                if i == max_retries - 1:
                    logger("✗ Signup page not changed", level=level+1)
                    # Even if we timed out, we return false but maybe we should default to suspecting failure
                    return False
                
                time.sleep(2)
            except Exception as e:
                logger(f"✗ Error checking current page URL: {format_error(e)}", level=level+1)
                time.sleep(2)

        logger(f"→ Final URL: {current_url}", level=level+1)
        
        self.__save_screenshot_and_page_html(level=level+1)
        
        if "suspended" in current_url.lower():
            self.account_data['status'] = 'suspended'
            logger("✗ Account suspended", level=level+1)
        elif "challenge" in current_url.lower():
             self.account_data['status'] = 'challenge'
             logger("⚠ Account challenged", level=level+1)
        else:
            self.account_data['status'] = 'active'
            logger("✓ Account created successfully", level=level+1)


    def __verify_page_has_content(self, timeout=30, level: int = 0):
        """Verify that the page has actual content and is not blank/white."""
        print("  ")
        logger("[######] Verifying page has content...", level=level)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if page has meaningful content
                body_text = self.page.evaluate("() => document.body.innerText")
                body_html = self.page.evaluate("() => document.body.innerHTML")
                
                # Check if body has substantial content
                if body_text and len(body_text.strip()) > 50:
                    logger("✓ Page has content", level=level+1)
                    return True
                
                # Check if there are visible elements
                if body_html and len(body_html) > 1000:
                    logger("✓ Page has HTML content", level=level+1)
                    return True
                
                logger(f"→ Page appears empty, waiting... ({int(time.time() - start_time)}s)", level=level+1)
                time.sleep(2)
                
            except Exception as e:
                logger(f"→ Error checking content: {format_error(e)}", level=level+1)
                time.sleep(2)
        
        logger("✗ Page still appears empty after timeout", level=level+1)
        return False
    

    def __launch_browser(self, level: int = 0):
        """Launch browser."""
        print("  ")
        logger("[######] Launching browser...", level=level)
        
        try:
            self.browser = self.playwright.chromium.launch(
                headless=HEADLESS,
                args=ARGS,
                executable_path=CHROME_PATH
            )
            
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
    

    def __open_instagram_signup(self, level: int = 0):
        """Open Instagram signup page."""
        print("  ")
        logger("[######] Opening Instagram signup page...", level=level)
        
        for load_attempt in range(1, MAX_LOAD_ATTEMPTS_FOR_OPENING_INSTAGRAM_SIGNUP + 1):
            try:
                self.page.goto(INSTAGRAM_SIGNUP_URL, timeout=60000)
                
                # Wait for network to be idle
                self.page.wait_for_load_state('networkidle', timeout=30000)

                # Additional wait for JavaScript to render
                time.sleep(3)
                    
                # Verify page has actual content
                if self.__verify_page_has_content(timeout=20, level=level+1):
                    logger("✓ Instagram signup page opened successfully", level=level+1)
                    return True
                else:
                    # Take screenshot of blank page
                    self.__save_screenshot_and_page_html(level=level+1)
                    
                    if load_attempt < MAX_LOAD_ATTEMPTS_FOR_OPENING_INSTAGRAM_SIGNUP:
                        time.sleep(2)
                
            except Exception as e:
                logger(f"✗ Error opening Instagram signup page: {format_error(e)}", level=level+1)
                if load_attempt < MAX_LOAD_ATTEMPTS_FOR_OPENING_INSTAGRAM_SIGNUP:
                    time.sleep(2)
        
        logger(f"✗ Failed to open Instagram signup page after {MAX_LOAD_ATTEMPTS_FOR_OPENING_INSTAGRAM_SIGNUP} attempts", level=level+1)
        return False


    def step_1_enter_email(self, level: int = 0):
        """Step 1: Enter email address and click Next."""
        print("  ")
        logger("[Step 1] Creating and Entering email address...", level=level)

        email_address = self.__get_email_address(level=level+1)
        if not email_address:
            return False

        self.__save_screenshot_and_page_html(level=level+1)
        
        if not self.__fill_field(EMAIL_FIELD_SELECTOR, email_address, name="Email Field", level=level+1):
            return False
        
        time.sleep(1)
        
        if not self.__click_button_with_dispatch(NEXT_BUTTON_SELECTOR, name="Next Button", level=level+1):
            return False
        
        return True
        

    def step_2_enter_verification_code(self, retry_number=1, level: int = 0):
        """Step 2: Wait for email, extract code, and submit."""
        print("  ")
        logger("[Step 2] Waiting for verification code and Entering it...", level=level)

        self.__save_screenshot_and_page_html(level=level+1)
        
        code = self.__wait_for_verification_code(level=level+1)
        if not code:
            return False
        
        if not self.__fill_field(VERIFICATION_CODE_SELECTOR, code, name="Verification Code Field", level=level+1):
            return False
        
        time.sleep(1)
        
        if not self.__click_button_with_dispatch(NEXT_BUTTON_SELECTOR, name="Next Button", level=level+1):
            return False

        # Check for error messages
        error_msg = self.__check_for_error_message(level=level+1)
        if error_msg:
            if retry_number > 3:
                logger(f"✗ Maximum retry attempts reached: {retry_number}", level=level+1)
                return False

            if not self.__click_change_email_button_for_retry_with_new_email(level=level+1):
                return False
            
            if not self.step_1_enter_email(level=level):
                return False

            if not self.step_2_enter_verification_code(retry_number + 1, level=level):
                return False
        else:
            return True
        
        return True


    def step_3_enter_password(self, level: int = 0):
        """Step 3: Enter password and click Next."""
        print("  ")
        logger("[Step 3] Entering password...", level=level)

        self.__save_screenshot_and_page_html(level=level+1)
        
        if not self.__fill_field(PASSWORD_SELECTOR, self.account_data['password'], name="Password Field", log_value=False, level=level+1):
            return False
        
        time.sleep(1)
        
        if not self.__click_button_with_dispatch(NEXT_BUTTON_SELECTOR, name="Next Button", level=level+1):
            return False
        
        return True


    def step_4_enter_birthdate(self, level: int = 0):
        """Step 4: Enter birthdate and click Next."""
        print("  ")
        logger("[Step 4] Entering birthdate...", level=level)
        
        self.__save_screenshot_and_page_html(level=level+1)
        
        if not self.__fill_field(BIRTHDATE_SELECTOR, self.account_data['birth_date'], name="Birthdate Field", level=level+1):
            return False
        
        time.sleep(1)
        
        if not self.__click_button_with_dispatch(NEXT_BUTTON_SELECTOR, name="Next Button", level=level+1):
            return False
        
        return True

    def step_5_enter_name(self, level: int = 0):
        """Step 5: Enter full name and click Next."""
        print("  ")
        logger("[Step 5] Entering full name...", level=level)
        
        self.__save_screenshot_and_page_html(level=level+1)
        
        if not self.__fill_field(NAME_SELECTOR, self.account_data['complete_name'], name="Name Field", level=level+1):
            return False
        
        time.sleep(1)
        
        if not self.__click_button_with_dispatch(NEXT_BUTTON_SELECTOR, name="Next Button", level=level+1):
            return False
        
        return True

    def step_6_enter_username(self, level: int = 0):
        """Step 6: Enter username and click Next."""
        print("  ")
        logger("[Step 6] Entering username...", level=level)
        
        self.__save_screenshot_and_page_html(level=level+1)
        
        if not self.__fill_field(USERNAME_SELECTOR, self.account_data['profile_name'], name="Username Field", level=level+1):
            return False
        
        time.sleep(1)
        
        if not self.__click_button_with_dispatch(NEXT_BUTTON_SELECTOR, name="Next Button", level=level+1):
            return False
        
        return True

    def step_7_accept_terms(self, level: int = 0):
        """Step 7: Accept terms and conditions."""
        print("  ")
        logger("[Step 7] Accepting terms...", level=level)

        self.__save_screenshot_and_page_html(level=level+1)
        
        if not self.__click_button_with_dispatch(ACCEPT_BUTTON_SELECTOR, name="Accept Button", level=level+1):
            return False
        
        return True


    def run_flow_with_retry(self, max_retries=MAX_RETRIES_FOR_ACCOUNT_CREATION, level: int = 0):
        """Execute the complete account creation flow with retry logic."""
        print("  ")
        logger("Instagram Mobile Account Generator (With Retry)", level=level)

        for attempt in range(1, max_retries + 1):
            logger(f"→ Attempt {attempt}/{max_retries}", level=level+1)
            
            if self.run_flow(level=level+1):
                return True
            
            if attempt < max_retries:
                time.sleep(2)
        
        # If we get here, all retries failed
        logger(f"✗ Failed to create account after {max_retries} attempts", level=level+1)
        return False


    def run_flow(self, level: int = 0):
        """Execute the complete account creation flow."""
        print("  ")
        logger("Instagram Mobile Account Generator", level=level)
        
        # Use context manager for better lifecycle management
        with sync_playwright() as p:
            self.playwright = p
            
            try:
                # Generate account info
                self.__generate_account_info(level=level+1)
                
                # Launch browser
                if not self.__launch_browser(level=level+1):
                    return False
                
                # Open Instagram signup page
                if not self.__open_instagram_signup(level=level+1):
                    return False
                    
                logger("✓ Ready to start signup process", level=level+1)
                
                # Execute signup steps
                if not self.step_1_enter_email(level=level+1):
                    return False
                
                self.natural_delay(2, 4)

                # Check this element if exists
                # [role='button'][aria-label='S’inscrire avec une adresse e-mail']
                # if exists, click it
                if self.__click_button_with_dispatch("[role='button'][aria-label='S’inscrire avec une adresse e-mail']", name="Sign In with Email Button", level=level+1):
                    logger("✓ Clicked Sign In with Email Button", level=level+1)
                    self.natural_delay(2, 4)
                    if not self.step_1_enter_email(level=level+1):
                        return False
                else:
                    logger("✗ Sign In with Email Button not found", level=level+1)

                self.natural_delay(2, 4)

                if not self.step_2_enter_verification_code(level=level+1):
                    return False
                
                self.natural_delay(2, 5)

                if not self.step_3_enter_password(level=level+1):
                    return False
                
                self.natural_delay(2, 4)

                if not self.step_4_enter_birthdate(level=level+1):
                    return False
                
                self.natural_delay(2, 4)

                if not self.step_5_enter_name(level=level+1):
                    return False
                
                self.natural_delay(2, 4)

                if not self.step_6_enter_username(level=level+1):
                    return False
                
                self.natural_delay(1, 3)

                if not self.step_7_accept_terms(level=level+1):
                    return False
                    
                # Check final status
                self.__check_account_status(max_retries=100, level=level+1)
                    
                # Save account data
                self.__save_account_to_json(level=level+1)
                    
                # Take final screenshot
                self.__save_screenshot_and_page_html(level=level+1)
                    
                logger("✓ Flow Completed Successfully!", level=level+1)
                    
                # Success - exit retry loop
                return True
                    
            except Exception as e:
                logger(f"✗ Failed to create account: {format_error(e)}", level=level+1)
                self.__save_screenshot_and_page_html()
                return False
            
            finally:
                # Cleanup browser resources
                try:
                    if self.browser:
                        input("\nPress Enter to close the browser...")
                        self.browser.close()
                except Exception as e:
                    logger(f"✗ Error during cleanup: {format_error(e)}", level=level+1)


if __name__ == "__main__":
    generator = InstagramMobileGenerator()
    generator.run_flow_with_retry()

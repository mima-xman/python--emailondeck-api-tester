import random
import string
import json
import time
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError
from fake_useragent import UserAgent
from EmailOnDeck import EmailOnDeck

class InstagramAccountGenerator:
    def __init__(self, use_tor=False):
        self.use_tor = use_tor
        self.ua = UserAgent()
        self.email_service = EmailOnDeck(use_tor=use_tor)
        self.account_data = {}

    def generate_account_info(self):
        """Generates random account information."""
        # 1. Password (Hard: Upper, Lower, Digits, Symbols)
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(12))

        # 2. Name (First Last)
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"

        # 3. Username
        # "CompleteName without space and lower.miamore complete"
        # Interpreting as: lowercase complete name + dot + random suffix to ensure uniqueness
        username_base = f"{first_name}{last_name}".lower()
        username_suffix = 'miamore'
        username = f"{username_base}.{username_suffix}"

        # 4. Birth Date (< 1999)
        year = random.randint(1980, 1998)
        month = random.randint(1, 12)
        day = random.randint(1, 28)

        self.account_data = {
            "email_address": None,
            "email_token": None,
            "password": password,
            "complete_name": full_name,
            "profile_name": username, # User called it Profile Name in prompt, usually functionality is username
            "birth_date": {"day": str(day), "month": str(month), "year": str(year)},
            "birth_date": {"day": str(day), "month": str(month), "year": str(year)},
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        return self.account_data

    def save_account_to_json(self, filename="instagram_accounts.json"):
        """Saves account data to a JSON file."""
        try:
            # We want to add Token to the saved data if available
            # The prompt asks for { email_address, email_token, password, complete_name, profile_name, birtdate, created_at }
            
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []
            
            if not isinstance(data, list): 
                data = [data]
                
            data.append(self.account_data)
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Account saved to {filename}")
        except Exception as e:
            print(f"Error saving account: {e}")

    def fill_birthdate(self, page):
        """Fills the birthdate fields using multiple potential selectors."""
        month = str(self.account_data['birth_date']['month'])
        day = str(self.account_data['birth_date']['day'])
        year = str(self.account_data['birth_date']['year'])

        # Selectors to try for Month
        month_selectors = ['select[title="Month:"]', 'select[aria-label="Month"]', 'select[name="birthday_month"]']
        month_found = False
        for selector in month_selectors:
            if page.is_visible(selector):
                try:
                    page.select_option(selector, value=month)
                    print(f"Filled Month using {selector}: {month}")
                    month_found = True
                except Exception as e:
                    print(f"Month fill debug (skipping): {str(e)}")
                    pass
                break
        
        # Selectors to try for Day
        day_selectors = ['select[title="Day:"]', 'select[aria-label="Day"]', 'select[name="birthday_day"]']
        for selector in day_selectors:
            if page.is_visible(selector):
                try:
                    page.select_option(selector, value=day)
                    print(f"Filled Day using {selector}: {day}")
                except Exception as e:
                    print(f"Day fill debug (skipping): {str(e)}")
                    pass
                break
        
        # Selectors to try for Year
        year_selectors = ['select[title="Year:"]', 'select[aria-label="Year"]', 'select[name="birthday_year"]']
        for selector in year_selectors:
            if page.is_visible(selector):
                try:
                    page.select_option(selector, value=year)
                    print(f"Filled Year using {selector}: {year}")
                except Exception as e:
                    print(f"Year fill debug (skipping): {str(e)}")
                    pass
                break
        
        return month_found

    def check_and_fill_email(self, page):
        """Checks if email needs to be filled and handles switching from Phone mode."""
        if self.setup_status['email']:
            return False

        # 1. Attempt to switch to Email mode if "Sign up with email" is visible
        try:
            switch_btn = page.locator('button, a').filter(has_text="Sign up with email").first
            if switch_btn.is_visible():
                print("Detected Phone mode. Switching to Email...")
                switch_btn.click()
                page.wait_for_timeout(1000)
            else:
                print("Phone mode not detected. Skipping switch.")
        except Exception as e:
            print(f"Switch to Email debug (skipping): {str(e)}")
            pass

        # 2. Try filling Email
        try:
            # Strategies: Label text, distinct names, aria-labels
            inputs_to_try = [
                page.get_by_label("Mobile number or email"),
                page.get_by_label("Email"),
                page.locator('input[name="emailOrPhone"]'),
                page.locator('input[name="email"]'),
                page.locator('input[type="email"]')
            ]
            
            for inp in inputs_to_try:
                if inp.is_visible():
                    print(f"Filling Email using selector: {inp}")
                    inp.fill(self.account_data['email_address'])
                    self.setup_status['email'] = True
                    return True
        except Exception as e:
            print(f"Email fill debug (skipping): {str(e)}")
            pass
        
        return False

    def check_and_fill_fullname(self, page):
        if self.setup_status['fullname']:
            return False
        
        try:
            inputs = [
                page.get_by_label("Full name"), # Case sensitive in some contexts, but usually "Full Name" or "Full name"
                page.get_by_label("Full Name"),
                page.locator('input[name="fullName"]'),
                page.locator('input[aria-label="Full Name"]')
            ]
            for inp in inputs:
                if inp.is_visible():
                    print(f"Filling Full Name: {self.account_data['complete_name']}")
                    inp.fill(self.account_data['complete_name'])
                    self.setup_status['fullname'] = True
                    return True
        except Exception as e:
            print(f"Full name fill debug (skipping): {str(e)}")
            pass
        return False

    def check_and_fill_password(self, page):
        if self.setup_status['password']:
            return False
            
        try:
            inputs = [
                page.get_by_label("Password"),
                page.locator('input[name="password"]'),
                page.locator('input[aria-label="Password"]')
            ]
            for inp in inputs:
                if inp.is_visible():
                    first_char = self.account_data['password'][0]
                    last_char = self.account_data['password'][-1]
                    password_len = len(self.account_data['password'])
                    print(f"Filling Password: {first_char}{'*'*password_len-2}{last_char}")
                    inp.fill(self.account_data['password'])
                    self.setup_status['password'] = True
                    return True
        except Exception as e:
            print(f"Password fill debug (skipping): {str(e)}")
            pass
        return False

    def check_and_fill_username(self, page):
        if self.setup_status['username']:
            return False
            
        try:
            inputs = [
                page.get_by_label("Username"),
                page.locator('input[name="username"]'),
                page.locator('input[aria-label="Username"]')
            ]
            for inp in inputs:
                if inp.is_visible():
                    val = inp.input_value()
                    if not val:
                        print(f"Filling Username: {self.account_data['profile_name']}")
                        inp.fill(self.account_data['profile_name'])
                        self.setup_status['username'] = True
                        return True
                    else:
                        # Already has a value (maybe auto-generated or pre-filled)
                        print(f"Username already present: {val}")
                        self.account_data['profile_name'] = val
                        self.setup_status['username'] = True
                        return True
        except Exception as e:
            print(f"Username fill debug (skipping): {str(e)}")
            pass
        return False

    def check_and_fill_birthdate_step(self, page):
        if self.setup_status['birthdate']:
            return False
        
        # Check if selectors are visible
        # Using the helper fill_birthdate which returns True if it found/filled something
        if self.fill_birthdate(page):
            print("Birthdate filled.")
            self.setup_status['birthdate'] = True
            return True
        return False

    def orchestrate_signup(self, page):
        """Loops through steps until verification code is asked."""
        
        self.setup_status = {
            'email': False,
            'fullname': False,
            'password': False,
            'username': False,
            'birthdate': False
        }
        
        max_loops = int(os.getenv("MAX_LOOPS", 20))
        loop_count = 0
        
        while loop_count < max_loops:
            print(f"--- Signup Loop {loop_count + 1} ---")
            loop_count += 1
            
            # Capture screenshot for debugging
            try:
                screenshot_path = f"debug_loop_{loop_count}_{int(time.time())}.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"Screenshot failed: {e}")
            
            # Wait for content to allow page transitions
            try:
                page.wait_for_load_state('networkidle', timeout=2000)
            except:
                print("Failed to wait for load state, skipping")
                pass
            
            # 0. Check for Verification Code Screen (Success)
            if page.is_visible('input[name="email_confirmation_code"]'):
                print("Verification Code Screen Detected!")
                return True
            
            # 1. Attempt to Fill Information
            actions_taken = False
            if self.check_and_fill_email(page): actions_taken = True
            if self.check_and_fill_fullname(page): actions_taken = True
            if self.check_and_fill_password(page): actions_taken = True
            if self.check_and_fill_username(page): actions_taken = True
            if self.check_and_fill_birthdate_step(page): actions_taken = True
            
            # 2. Attempt to Advance (Click Buttons)
            button_clicked = False
            try:
                # Prioritize Submit > Next > Sign Up
                # Explicitly exclude the 'Sign up with email' link logic here
                
                # Check for "Next" button
                next_btn = page.locator('button').filter(has_text="Next").first
                if next_btn.is_visible():
                    print("Clicking Next...")
                    next_btn.click()
                    button_clicked = True
                    
                # Check for "Sign Up" button (but filter out the 'switch to email' link/button if it looks like one)
                elif not button_clicked:
                    signup_btn = page.locator('button').filter(has_text="Sign Up").first
                    if signup_btn.is_visible():
                        # Simple check: ignore if it says "email" (e.g. "Sign up with email")
                        if "email" not in signup_btn.inner_text().lower():
                            print("Clicking Sign Up...")
                            signup_btn.click()
                            button_clicked = True
                
                # Check for generic Submit
                elif not button_clicked:
                    submit_btn = page.locator('button[type="submit"]').first
                    if submit_btn.is_visible():
                         print("Clicking Submit...")
                         submit_btn.click()
                         button_clicked = True

            except Exception as e:
                print(f"Button click debug (skipping): {str(e)}")
                pass
            
            if actions_taken or button_clicked:
                # Give time for reaction
                page.wait_for_timeout(3000)
            else:
                print("No actions taken in this loop. Waiting for elements...")
                # Maybe waiting for page load
                page.wait_for_timeout(2000)

        print("Flow Failed: Failed to reach verification screen after max loops.")
        return False

    def run_flow(self):
        """Orchestrates the account creation flow."""
        print("Starting Instagram Account Generation Flow...")
        
        # 1. Generate Info
        self.generate_account_info()
        print(f"Generated Info: {self.account_data['profile_name']}")

        # 2. Get Email
        print("Getting Email from EmailOnDeck...")
        email_address = self.email_service.get_email()
        if not email_address:
            raise Exception("Failed to generate email address.")
        
        self.account_data['email_address'] = email_address
        self.account_data['email_token'] = getattr(self.email_service, 'email_hash', 'N/A')
        
        print(f"Email: {email_address}")

        with sync_playwright() as p:
            # Launch Browser with anti-detection args
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    f'--user-agent={self.ua.random}'
                ]
            )
            context = browser.new_context(
                viewport={'width': 375, 'height': 648},
                locale='en-US',
                user_agent=self.ua.random # Redundant but safe
            )
            
            # Stealth: Remove webdriver property
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()

            try:
                # 3. Open Instagram Signup
                print("Opening Instagram Signup...")
                page.goto("https://www.instagram.com/accounts/signup/email/", timeout=60000)
                page.wait_for_load_state('networkidle')
                
                # Run the new Orchestrator
                if self.orchestrate_signup(page):
                     # 4. Email Verification Loop
                    print("Waiting for Verification Code Screen...")
                    
                    max_retries = 3
                    success = False
    
                    for attempt in range(max_retries):
                        print(f"Verification Attempt {attempt + 1}/{max_retries}")
                        
                        # Wait for email
                        print("Checking for email...")
                        code = None
                        email_wait_start = time.time()
                        while time.time() - email_wait_start < 120: # 2 mins wait for email
                            # Get latest message
                            msg = self.email_service.wait_for_email(timeout=5)
                            if msg:
                                print(f"Email Subject: {msg.subject}")
                                # Try subject
                                match = re.search(r'\b\d{6}\b', msg.subject)
                                if match:
                                    code = match.group(0)
                                else:
                                    # Try content
                                    content = self.email_service.get_content(msg.msg_id)
                                    match = re.search(r'\b\d{6}\b', str(content))
                                    if match:
                                        code = match.group(0)
                                
                                if code:
                                    print(f"Code found: {code}")
                                    break
                            time.sleep(5)
                        
                        if not code:
                            print("No code received in time.")
                            if attempt < max_retries - 1:
                                print("Clicking Resend Code...")
                                try:
                                    page.click('text="Get a new code"') 
                                except:
                                    print("Could not find Resend button.")
                            continue
    
                        # Fill Code
                        print("Entering code...")
                        page.fill('input[name="email_confirmation_code"]', "") 
                        page.fill('input[name="email_confirmation_code"]', code)
                        page.click('div[role="button"]:has-text("Next")') 
    
                        try:
                            error_element = page.wait_for_selector('p[role="alert"], div[role="alert"]', timeout=5000)
                            if error_element:
                                error_text = error_element.text_content()
                                print(f"Error submitting code: {error_text}")
                                if attempt < max_retries - 1:
                                    print("Retrying with new code...")
                                    time.sleep(2)
                                    try:
                                        page.click('text="Get a new code"') 
                                    except:
                                        pass
                                    continue
                                else:
                                    raise Exception(f"Failed to verify code after retries: {error_text}")
                        except TimeoutError:
                            if page.is_visible('input[name="email_confirmation_code"]'):
                                pass
                            else:
                                success = True
                                break
                        
                        try:
                            page.wait_for_load_state('networkidle', timeout=5000)
                        except:
                            pass
                            
                        if not page.is_visible('input[name="email_confirmation_code"]'):
                             success = True
                             break
    
                    if not success:
                        raise Exception("Verification failed.")
    
                    # 5. Finalize
                    print("Verification successful (assumed). Waiting for completion...")
                    page.wait_for_timeout(5000)
                    
                    # Check for Suspended Status
                    current_url = page.url
                    print(f"Current URL: {current_url}")
                    
                    if "suspended" in current_url:
                        print("Account Suspended detected.")
                        self.account_data['status'] = 'suspended'
                    else:
                        self.account_data['status'] = 'active'
    
                    self.save_account_to_json()
                    print("Flow Completed Successfully.")
                else:
                    raise Exception("Failed to reach verification screen after max loops.")
                
            except Exception as e:
                print(f"Flow Failed: {e}")
                timestamp = int(time.time())
                screenshot_path = f"error_{timestamp}.png"
                error_html_path = f"error_page_{timestamp}.html"
                try:
                    page.screenshot(path=screenshot_path)
                    print(f"Saved error screenshot: {screenshot_path}")
                    
                    with open(error_html_path, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    print(f"Saved error HTML content: {error_html_path}")
                except:
                    pass
                raise e
            finally:
                browser.close()

if __name__ == "__main__":
    generator = InstagramAccountGenerator()
    generator.run_flow()

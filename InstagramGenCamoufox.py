import random
import string
import json
import time
import os
import re
from datetime import datetime
from camoufox.sync_api import Camoufox
from fake_useragent import UserAgent
from EmailOnDeck import EmailOnDeck
from utils import logger



class InstagramAccountGenerator:
    def __init__(self, use_tor=False):
        self.use_tor = use_tor
        self.ua = UserAgent()
        self.email_service = EmailOnDeck(use_tor=use_tor)
        self.account_data = {}

    def human_delay(self, min_ms=500, max_ms=1500):
        """Introduces a random human-like delay."""
        time.sleep(random.uniform(min_ms, max_ms) / 1000)

    def human_type(self, page, selector_or_locator, text, min_delay_ms=50, max_delay_ms=150):
        """Simulates human typing with random delays between characters."""
        if isinstance(selector_or_locator, str):
            locator = page.locator(selector_or_locator)
        else:
            locator = selector_or_locator

        if not locator.is_visible():
            return

        locator.focus()
        # Clear field if possible
        try:
             locator.fill("")
        except:
             pass
             
        for char in text:
            page.keyboard.type(char, delay=random.randint(min_delay_ms, max_delay_ms))
            time.sleep(random.uniform(0.02, 0.08))

    def human_click(self, page, selector_or_locator):
        """Simulates a human click with a small delay before the action."""
        if isinstance(selector_or_locator, str):
            locator = page.locator(selector_or_locator)
        else:
            locator = selector_or_locator

        if not locator.is_visible():
            return False

        # Simulate small mouse wiggle/move to element if wanted
        # page.mouse.move(random.randint(0, 100), random.randint(0, 100)) 
        
        self.human_delay(300, 800)
        locator.click()
        return True

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
            "profile_name": username,
            "birth_date": {"day": str(day), "month": str(month), "year": str(year)},
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        return self.account_data

    def save_account_to_json(self, filename="instagram_accounts.json", level: int = 0):
        """Saves account data to a JSON file."""
        try:
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
            logger(f"✓ Account saved to {filename}", level=level)
        except Exception as e:
            logger(f"✗ Error saving account: {e}", level=level)

    def _fill_birthdate_strategy_custom(self, page, month_full, day, year):
        """Strategy 1: Check for custom ARIA comboboxes."""
        try:
            # Month
            month_box = page.locator('div[role="combobox"]').filter(has_text=re.compile(r"^Month$", re.IGNORECASE))
            if not month_box.is_visible():
                 month_box = page.locator('div[role="combobox"]').filter(has_text="Month")
            
            if month_box.count() == 0 or not month_box.first.is_visible():
                return False

            print(f"Found Custom Month Combobox. Clicking...")
            self.human_click(page, month_box.first)
            
            option = page.locator(f'div[role="option"]').filter(has_text=re.compile(f"^{month_full}$", re.IGNORECASE)).first
            if not option.is_visible():
                 option = page.locator(f'div[role="button"], span').filter(has_text=month_full).first

            if not option.is_visible():
                return False
            self.human_click(page, option)
            
            # Day
            day_box = page.locator('div[role="combobox"]').filter(has_text=re.compile(r"^Day$", re.IGNORECASE))
            if not day_box.is_visible():
                day_box = page.locator('div[role="combobox"]').filter(has_text="Day")
            
            if day_box.count() == 0 or not day_box.first.is_visible():
                return False

            self.human_click(page, day_box.first)
            option = page.locator(f'div[role="option"]').filter(has_text=re.compile(f"^{day}$", re.IGNORECASE)).first
            if not option.is_visible():
                 option = page.locator(f'div[role="button"], span').filter(has_text=re.compile(f"^{day}$")).first
            
            if not option.is_visible():
                return False
            self.human_click(page, option)

            # Year
            year_box = page.locator('div[role="combobox"]').filter(has_text=re.compile(r"^Year$", re.IGNORECASE))
            if not year_box.is_visible():
                year_box = page.locator('div[role="combobox"]').filter(has_text="Year")
            
            if year_box.count() == 0 or not year_box.first.is_visible():
                return False

            self.human_click(page, year_box.first)
            option = page.locator(f'div[role="option"]').filter(has_text=year).first
            if not option.is_visible():
                option = page.locator(f'div[role="button"], span').filter(has_text=year).first
                
            if not option.is_visible():
                return False
            self.human_click(page, option)
            
            return True
            
        except Exception as e:
            print(f"Custom birthdate fill failed: {e}")
            return False

    def _fill_birthdate_strategy_standard(self, page, month, day, year):
        """Strategy 2: Fallback to standard Selectors."""
        try:
            # Month
            month_selectors = ['select[title="Month:"]', 'select[aria-label="Month"]', 'select[name="birthday_month"]']
            month_set = False
            for selector in month_selectors:
                if page.is_visible(selector):
                    page.select_option(selector, value=month)
                    month_set = True
                    break
            if not month_set: return False
            
            # Day
            day_selectors = ['select[title="Day:"]', 'select[aria-label="Day"]', 'select[name="birthday_day"]']
            day_set = False
            for selector in day_selectors:
                if page.is_visible(selector):
                    page.select_option(selector, value=day)
                    day_set = True
                    break
            if not day_set: return False
            
            # Year
            year_selectors = ['select[title="Year:"]', 'select[aria-label="Year"]', 'select[name="birthday_year"]']
            year_set = False
            for selector in year_selectors:
                if page.is_visible(selector):
                    page.select_option(selector, value=year)
                    year_set = True
                    break
            if not year_set: return False

            return True

        except Exception as e:
            print(f"Standard birthdate fill failed: {e}")
            return False

    def fill_birthdate(self, page):
        """Fills the birthdate fields."""
        month_int = int(self.account_data['birth_date']['month'])
        day = str(self.account_data['birth_date']['day'])
        year = str(self.account_data['birth_date']['year'])
        
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        month_full = month_names[month_int - 1]
        
        if self._fill_birthdate_strategy_custom(page, month_full, day, year):
            return True
        
        month_str = str(month_int)
        if self._fill_birthdate_strategy_standard(page, month_str, day, year):
            return True
            
        return False

    def check_and_fill_email(self, page):
        if self.setup_status['email']:
            return False

        try:
            switch_btn = page.locator('button, a').filter(has_text="Sign up with email").first
            if switch_btn.is_visible():
                self.human_click(page, switch_btn)
                page.wait_for_timeout(1000)
        except:
            pass

        try:
            inputs_to_try = [
                page.get_by_label("Mobile number or email"),
                page.get_by_label("Email"),
                page.locator('input[name="emailOrPhone"]'),
                page.locator('input[name="email"]'),
                page.locator('input[type="email"]')
            ]
            
            for inp in inputs_to_try:
                if inp.is_visible():
                    print(f"Typing Email humanly...")
                    self.human_type(page, inp, self.account_data['email_address'])
                    self.setup_status['email'] = True
                    return True
        except Exception as e:
            print(f"Email fill debug: {e}")
        
        return False

    def check_and_fill_fullname(self, page):
        if self.setup_status['fullname']:
            return False
        
        try:
            inputs = [
                page.get_by_label("Full name"),
                page.get_by_label("Full Name"),
                page.locator('input[name="fullName"]'),
                page.locator('input[aria-label="Full Name"]')
            ]
            for inp in inputs:
                if inp.is_visible():
                    print(f"Typing Full Name humanly...")
                    self.human_type(page, inp, self.account_data['complete_name'])
                    self.setup_status['fullname'] = True
                    return True
        except:
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
                    print(f"Typing Password humanly...")
                    self.human_type(page, inp, self.account_data['password'])
                    self.setup_status['password'] = True
                    return True
        except:
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
                        print(f"Typing Username humanly...")
                        self.human_type(page, inp, self.account_data['profile_name'])
                        self.setup_status['username'] = True
                        return True
                    else:
                        print(f"Username already present: {val}")
                        self.account_data['profile_name'] = val
                        self.setup_status['username'] = True
                        return True
        except:
            pass
        return False

    def check_and_fill_birthdate_step(self, page):
        if self.setup_status['birthdate']:
            return False
        if self.fill_birthdate(page):
            self.setup_status['birthdate'] = True
            return True
        return False

    def orchestrate_signup(self, page):
        self.setup_status = {'email': False, 'fullname': False, 'password': False, 'username': False, 'birthdate': False}
        max_loops = int(os.getenv("MAX_LOOPS", 20))
        loop_count = 0
        
        while loop_count < max_loops:
            print(f"--- Signup Loop {loop_count + 1} ---")
            loop_count += 1
            
            try:
                page.wait_for_load_state('networkidle', timeout=2000)
            except:
                pass
            
            if page.is_visible('input[name="email_confirmation_code"]'):
                print("Verification Code Screen Detected!")
                return True
            
            actions_taken = False
            if self.check_and_fill_email(page): actions_taken = True
            if self.check_and_fill_fullname(page): actions_taken = True
            if self.check_and_fill_password(page): actions_taken = True
            if self.check_and_fill_username(page): actions_taken = True
            if self.check_and_fill_birthdate_step(page): actions_taken = True
            
            button_clicked = False
            try:
                # 1. Submit
                submit_sel = page.locator('button, div[role="button"]').filter(has_text=re.compile(r"^Submit$", re.IGNORECASE)).first
                if submit_sel.is_visible():
                    print("Clicking Submit humanly...")
                    self.human_click(page, submit_sel)
                    button_clicked = True
                    
                # 2. Next
                elif not button_clicked:
                    next_sel = page.locator('button, div[role="button"]').filter(has_text=re.compile(r"^Next$", re.IGNORECASE)).first
                    if next_sel.is_visible():
                        print("Clicking Next humanly...")
                        self.human_click(page, next_sel)
                        button_clicked = True
                        
                # 3. Sign Up
                elif not button_clicked:
                    signup_sel = page.locator('button, div[role="button"]').filter(has_text=re.compile(r"^Sign Up$", re.IGNORECASE)).first
                    if signup_sel.is_visible():
                        btn_text = signup_sel.inner_text().lower()
                        if "email" not in btn_text and "phone" not in btn_text:
                            print("Clicking Sign Up humanly...")
                            self.human_click(page, signup_sel)
                            button_clicked = True
                
                # Fallback to generic submit
                if not button_clicked:
                    gen_submit = page.locator('button[type="submit"]').first
                    if gen_submit.is_visible():
                        print("Clicking Generic Submit humanly...")
                        self.human_click(page, gen_submit)
                        button_clicked = True

            except:
                pass
            
            if actions_taken or button_clicked:
                page.wait_for_timeout(3000)
            else:
                page.wait_for_timeout(2000)

        return False

    def run_flow(self):
        print("Starting Instagram Account Generation Flow (Human-Like Approach)...")
        self.generate_account_info()
        email_address = self.email_service.get_email()
        if not email_address:
            raise Exception("Failed to generate email.")
        
        self.account_data['email_address'] = email_address
        self.account_data['email_token'] = getattr(self.email_service, 'email_hash', 'N/A')
        print(f"Email: {email_address}")

        try:
            # Use headless=False in CI via XVFB, or true for local speed
            is_headless = os.getenv("HEADLESS", "false").lower() == "true"
            is_geoip = os.getenv("GEOIP", "false").lower() == "true"
            with Camoufox(headless=is_headless, geoip=is_geoip) as browser:
                page = browser.new_page(viewport={"width": 375, "height": 648})
                time.sleep(2)

                try:
                    signup_url = "https://www.instagram.com/accounts/emailsignup/"
                    page_loaded = False
                    
                    for i in range(3):
                        try:
                            print(f"Loading page (Attempt {i+1}/3)...")
                            page.goto(signup_url, timeout=60000)
                            page.wait_for_load_state('networkidle')
                            content = page.content()
                            if len(content) < 500 or "<body></body>" in content.replace(" ", ""):
                                page.wait_for_timeout(2000)
                                continue
                            page_loaded = True
                            print("Page loaded successfully.")
                            break
                        except:
                            page.wait_for_timeout(2000)
                    
                    if not page_loaded:
                        raise Exception("Failed to load page (Blank detected).")

                    if self.orchestrate_signup(page):
                        print("Waiting for Verification Code Screen...")
                        # Verification logic remains similar but uses human helpers for inputs
                        # ... (omitted for brevity in this example but kept in full file) ...
                        # (Note: I'll include the full verification logic below)
                        
                        max_retries = 3
                        success = False
                        for attempt in range(max_retries):
                            print(f"Verification Attempt {attempt + 1}/{max_retries}")
                            code = None
                            email_wait_start = time.time()
                            while time.time() - email_wait_start < 120:
                                msg = self.email_service.wait_for_email(timeout=5)
                                if msg:
                                    match = re.search(r'\b\d{6}\b', msg.subject)
                                    if match: code = match.group(0)
                                    else:
                                        content = self.email_service.get_content(msg.msg_id)
                                        match = re.search(r'\b\d{6}\b', str(content))
                                        if match: code = match.group(0)
                                    if code: break
                                time.sleep(5)
                            
                            if not code:
                                if attempt < max_retries - 1:
                                    try: page.click('text="Get a new code"') 
                                    except: pass
                                continue
        
                            print(f"Entering code humanly: {code}")
                            code_input = page.locator('input[name="email_confirmation_code"]')
                            self.human_type(page, code_input, code)
                            
                            next_btn = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")').first
                            self.human_click(page, next_btn)
                            
                            try:
                                error_element = page.wait_for_selector('p[role="alert"], div[role="alert"]', timeout=5000)
                                if error_element:
                                    if attempt < max_retries - 1:
                                        time.sleep(2)
                                        try: page.click('text="Get a new code"') 
                                        except: pass
                                        continue
                                    else: raise Exception("Failed verification.")
                            except:
                                if not page.is_visible('input[name="email_confirmation_code"]'):
                                    success = True
                                    break
                        
                        if success:
                            print("Success! Finalizing...")
                            page.wait_for_timeout(5000)
                            if "suspended" in page.url:
                                self.account_data['status'] = 'suspended'
                            else:
                                self.account_data['status'] = 'active'
                            self.save_account_to_json()
                            print("Flow Completed.")
                        else:
                            raise Exception("Verification failed.")
                    else:
                        raise Exception("Failed to reach verification.")

                except Exception as e:
                    print(f"Flow Failed: {e}")
                    ts = int(time.time())
                    try:
                        page.screenshot(path=f"error_{ts}.png")
                        with open(f"error_page_{ts}.html", "w", encoding="utf-8") as f: f.write(page.content())
                    except: pass
                    raise e
        except Exception as outer_e:
            print(f"Critical error: {outer_e}")
            raise outer_e

if __name__ == "__main__":
    generator = InstagramAccountGenerator()
    generator.run_flow()

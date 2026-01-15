# +--------------------------------------+
# | Instagram Generator in Mobile config |
# +--------------------------------------+


# Instagram signup page URL
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/signup/email"

# Account information
FIRST_NAMES = ["Liam", "Emma", "Noah", "Olivia", "William", "Ava", "James", "Isabella", "Oliver", "Sophia", "Benjamin", "Mia"]
LAST_NAMES = ["Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White", "Harris", "Martin", "Thompson", "Young"]

# Account username suffix
USERNAME_SUFFIX = "miamore"

# Maximum wait time for verification code (in seconds)
MAX_WAIT_TIME_FOR_VERIFICATION_CODE = 120

# Browser settings
# VIEWPORT = { 'width': 375, 'height': 667 }
VIEWPORT = { 'width': 1024, 'height': 768 }
LOCALE = 'fr-FR'
USER_AGENT = 'Mozilla/5.0 (Linux; Android 12; SM-G975F Build/QP1A.190711.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36'
HEADLESS = False
ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-infobars',
    '--ignore-certificate-errors',
    f'--user-agent={USER_AGENT}'
]

# Maximum load attempts for opening Instagram signup page
MAX_LOAD_ATTEMPTS_FOR_OPENING_INSTAGRAM_SIGNUP = 3

# Maximum retries for account creation
MAX_RETRIES_FOR_ACCOUNT_CREATION = 3

# Maximum retries for account status check
MAX_RETRIES_FOR_ACCOUNT_STATUS_CHECK = 5

# --- Selectors ---
ERROR_MESSAGE_SELECTOR = "div > div > div > div > div > div > div > div > div > div > div > div > div > div:nth-child(3) > div > div > div > div > div > div:nth-child(2) > div > div > div > div > div:nth-child(2) > div > div > span"
NEXT_BUTTON_SELECTOR = "[role='button'][aria-label='Suivant'], div > div > div > div > div  > div > div > section > main > div > div > div > button"
# Step 1 (Email)
EMAIL_FIELD_SELECTOR = "input[type='email'][aria-label='Adresse e-mail']"
# Step 2 (Validation Code)
VERIFICATION_CODE_SELECTOR = "input[aria-label='Code de confirmation']"
DIDNT_RECEIVE_CODE_BUTTON_SELECTOR = "div > div > div > div > div > div > div > div > div > div > div > div > div > div:nth-child(3) > div > div > div > div > div > div:nth-child(3) > div > div > div:nth-child(2) > div > div > div"
CHANGE_EMAIL_BUTTON_SELECTOR = "div > div > div > div > div > div > div > div > div > div:nth-child(2) > div > div > div > div:nth-child(3) > div > div > div > div > div > div > div > div > div:nth-child(2) > div:nth-child(1) > div > div"
# Step 3 (Password)
PASSWORD_SELECTOR = "input[type='password'][aria-label='Mot de passe']"
# Step 4 (Birthdate)
BIRTHDATE_SELECTOR = "input[type='date']"
# Step 5 (Name)
NAME_SELECTOR = "input[type='text'][aria-label='Nom complet'], div > div > div > div > div > div > div > div > div > div > div > div > div > div:nth-child(3) > div > div > div > div:nth-child(1) > div > div:nth-child(2) > div > div > div > div > div:nth-child(2) > div:nth-child(2) > input, input[type='text']"
# Step 6 (Username)
USERNAME_SELECTOR = "input[type='text-no_suggestion'][aria-label='Nom de profil'], div > div > div > div > div > div > div > div > div > div > div > div > div > div:nth-child(3) > div > div > div > div:nth-child(1) > div > div:nth-child(2) > div > div > div > div > div:nth-child(2) > div:nth-child(2) > input, input[type='text-no_suggestion'], input[type='text']"
# Step 7 (Accept)
ACCEPT_BUTTON_SELECTOR = "div > div > div > div > div > div > div > div > div > div > div > div > div > div:nth-child(3) > div > div > div > div:nth-child(1) > div > div:nth-child(5) > div > div:nth-child(1) > div > div"

# --- Output Directories & Files ---
OUTPUT_DIR = "output"
INSTAGRAM_ACCOUNTS_INFO_FILENAME = "instagram_accounts_info.json"

# Brave Browser Path
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
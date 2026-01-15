# EmailOnDeck API Tester

A Python library and test suite for interacting with the EmailOnDeck temporary email service, with optional Tor support for anonymity.

## Features

- 📧 Create temporary email addresses
- 📬 Retrieve inbox messages
- 📖 Read email content
- 🔒 Optional Tor support for anonymous requests
- 🔄 Automatic retry logic with IP rotation
- 🤖 GitHub Actions workflow for automated testing

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Local Testing

```python
from EmailOnDeck import EmailOnDeck

# Create client with Tor
client = EmailOnDeck(use_tor=True, max_retries=3)

# Get email address
email = client.get_email()
print(f"Email: {email}")

# Wait for email
msg = client.wait_for_email(timeout=60)
if msg:
    print(f"From: {msg.sender}")
    print(f"Subject: {msg.subject}")
    
    # Get content
    content = client.get_content(msg.msg_id)
    print(content)
```

### Running the Test Script

You can run the test script locally with environment variables:

```bash
# With Tor (default)
python EmailOnDeckTest.py

# Without Tor
USE_TOR=false python EmailOnDeckTest.py

# Custom configuration
USE_TOR=true MAX_RETRIES=5 TIMEOUT=120 python EmailOnDeckTest.py
```

## GitHub Actions Workflow

This project includes a GitHub Actions workflow that allows you to manually test the EmailOnDeck API directly from GitHub.

### How to Run the Workflow

1. **Navigate to Actions Tab**
   - Go to your repository on GitHub
   - Click on the "Actions" tab

2. **Select the Workflow**
   - Find "Test EmailOnDeck API" in the workflows list
   - Click on it

3. **Run Workflow**
   - Click the "Run workflow" button
   - Configure the parameters:
     - **Use Tor**: Choose `true` or `false` (default: `false`)
     - **Max Retries**: Number of retry attempts (default: `3`)
     - **Timeout**: Seconds to wait for email (default: `60`)
   - Click "Run workflow"

4. **View Results**
   - The workflow will appear in the runs list
   - Click on it to see the execution logs
   - Check the "Run EmailOnDeck Test" step for output

### Workflow Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `use_tor` | Enable Tor for anonymous requests | `false` | `true`, `false` |
| `max_retries` | Maximum number of retry attempts | `3` | Any positive integer |
| `timeout` | Timeout for waiting for email (seconds) | `60` | Any positive integer |

### Workflow Features

- ✅ Automatic Python environment setup
- ✅ Dependency installation with caching
- ✅ Optional Tor installation and configuration
- ✅ Configurable test parameters
- ✅ Detailed execution logs
- ✅ Manual trigger only (workflow_dispatch)

## API Reference

### EmailOnDeck Class

#### Constructor

```python
EmailOnDeck(use_tor=False, tor_port=9150, tor_control_port=9151, max_retries=3)
```

- `use_tor`: Enable Tor proxy for requests
- `tor_port`: Tor SOCKS proxy port
- `tor_control_port`: Tor control port for IP rotation
- `max_retries`: Maximum retry attempts on failure

#### Methods

- `create_email()`: Create a new temporary email address
- `get_email()`: Get current email or create new one
- `get_messages()`: Retrieve all inbox messages
- `get_content(msg_id)`: Get email content by message ID
- `wait_for_email(timeout, interval)`: Wait for email to arrive

### Email Class

```python
@dataclass
class Email:
    msg_id: str      # Message ID
    sender: str      # Sender email address
    subject: str     # Email subject
    received: str    # Received timestamp
```

## Requirements

- Python 3.7+
- requests
- PySocks (for Tor support)
- stem (for Tor control)

## Tor Setup (Optional)

To use Tor for anonymous requests:

1. **Install Tor Browser** or **Tor Service**
   - Windows: Download from https://www.torproject.org/
   - Linux: `sudo apt-get install tor`
   - macOS: `brew install tor`

2. **Configure Tor** (if using Tor service)
   ```bash
   # Edit /etc/tor/torrc
   SocksPort 9150
   ControlPort 9151
   CookieAuthentication 0
   ```

3. **Start Tor**
   - Tor Browser: Just open it
   - Tor Service: `sudo systemctl start tor`

## Notes

- The EmailOnDeck service may have rate limits
- Tor support helps bypass rate limits by rotating IP addresses
- GitHub Actions workflow automatically sets up Tor when enabled
- Email addresses are temporary and expire after some time

## License

MIT License

import time
from stem import Signal
from stem.control import Controller
import requests
import pyotp



def logger(message: str, level: int = 0) -> None:
    space_text = "  " * level
    print(f"{space_text}{message}")


def format_error(e: Exception) -> str:
    """Format error message to be cleaner by removing call logs."""
    return str(e).split("Call log:")[0].strip()


def renew_tor(tor_control_port: int = 9151, tor_port: int = 9150, level: int = 0) -> bool:
    """Renew Tor identity"""
    try:
        with Controller.from_port(port=tor_control_port) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            time.sleep(5)
            logger("✓ Tor renewed", level=level)

            ip = None
            try:
                tor_proxies = {
                    "http": f"socks5://127.0.0.1:{tor_port}",
                    "https": f"socks5://127.0.0.1:{tor_port}"
                }
                ip = get_current_ip(proxies=tor_proxies, level=level)
            except:
                pass    
            
            return True, ip
    except Exception as e:
        logger(f"✗ Failed to renew Tor: {e}", level=level)
        return False, None


def get_current_ip(proxies: dict = {}, timeout: int = 10, level: int = 0) -> str:
    """Get current IP address"""
    try:
        services = [
            'https://ifconfig.me/ip',
            'https://icanhazip.com',
            'https://checkip.amazonaws.com',
            'https://ipinfo.io/ip',
            'https://ident.me'
        ]
        
        for service in services:
            try:
                response = requests.get(
                    service,
                    proxies=proxies,
                    timeout=timeout
                )

                if response.status_code == 200:
                    ip = response.text.strip()
                    logger(f"✓ Current IP: {ip}", level=level)
                    return ip
            except:
                continue
        
        logger("✗ Failed to get current IP", level=level)
        return None

    except Exception as e:
        logger(f"✗ Error getting IP: {format_error(e)}", level=level)
        return None


def get_2fa_code(secret: str):
    """Get 2FA code from secret"""
    totp = pyotp.TOTP(secret)
    code = totp.now()
    return code


if __name__ == "__main__":
    # 6KHUFEJDRK2DGVQV
    # WNC34H4G6ZHVLP43
    secret = "WNC34H4G6ZHVLP43"
    code = get_2fa_code(secret)
    print(f"Current 2FA code: {code}")
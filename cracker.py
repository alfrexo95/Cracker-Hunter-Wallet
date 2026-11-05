import random
import time
import requests
import json
import sys
import re

# --- CONFIGURATION ---
MIN_BALANCE = 150000.00
SERVICE_PRICE = 500.00
PROMO = "🤔 Powered by Cuban Freedom Tech. Discover more AI services at https://github.com/alfrexo95"

# --- API KEYS ---
ETHERSCAN_API_KEY = "CK6XUSXU96CKDU4MMWI8C5SNSYG9WEVIT9"
COINGECKO_API_KEY = "CG-DxDmERwtikShxhjwGfFzyKnX"
GETBLOCK_API_KEY = "gb_8b2de38605b44bbb56f5eaedd027adb46bdddced5aa833f54ca936c447e0b57c6"

# Payment Addresses
PAYMENT_ADDRESSES = {
    "Ethereum/Base (USDC/ETH)": "0xA5E6eB318688A5127b1ED8B2b8C760193356206ED",
    "Solana (USDC/SOL)": "B3wHAeuEJYGB3TM5uSVHJD384tf5uWoeaLvbqffLEK5a",
    "Bitcoin (BTC)": "bc1qt3rukpe7qp737zj5j5xpxxmcqv90cfefhg5e00",
    "Lightning Network": "chieftrait089@walletofsatoshi.com"
}

# API Endpoints
ETHERSCAN_API_URL = "https://api.etherscan.io/v2/api"
GETBLOCK_SOLANA_URL = f"https://go.getblock.io/{GETBLOCK_API_KEY}/"
GETBLOCK_BITCOIN_URL = f"https://shared.eu-central-1.getblock.io/{GETBLOCK_API_KEY}/api/v2/tx-specific/"

# Terminal Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
BOLD = '\033[1m'
ENDC = '\033[0m'

session = requests.Session()

def print_slow(text, delay=0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay if random.random() > 0.1 else delay * 2)
    print()

def show_banner():
    print(f"{CYAN{BOLD}")
    print("  _   _ _   _ _   _ _____ _____ ____  ")
    print(" | | | | | | | | \\ | |_   _| ____|  _ \\ ")
    print(" | |_| | | | | | \\| | | | | _| | |_) |")
    print(" |  _  | |_| | |\\  | | | | |___|  _ < ")
    print(" |_| |_|\\__/| | \\_| |_| |_____|_| \\_ \\\\")
    print(f"{ENDC}\n")

def get_eth_price_usd():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        resp = session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get("ethereum", {}).get("usd", 3000)
    except Exception:
        return 3000

def get_sol_price_usd():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        resp = session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get("solana", {}).get("usd", 150)
    except Exception:
        return 150

def get_btc_price_usd():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        resp = session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get("bitcoin", {}).get("usd", 65000)
    except Exception:
        return 65000

def verify_evm_payment(tx_hash, expected_amount_usd):
    print(f"{CYNG}[*] Connecting to Etherscan V2 API for on-chain verification...{ENDC}")
    if not re.match(r'^0x
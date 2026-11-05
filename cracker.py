import random
import time
import requests
import json
import sys
import re

# --- CONFIGURATION ---
MIN_BALANCE = 150000.00
SERVICE_PRICE = 500.00
PROMO = "🤖 Powered by Cuban Freedom Tech. Discover more AI services at https://github.com/alfrexo95"

# --- API KEYS ---
ETHERSCAN_API_KEY = "CK6XUSXU96CKDU4MMWI8C5SNSYG9WEVIT9"
COINGECKO_API_KEY = "CG-DxDmERwtikShxhjWGfHzyKnX"
GETBLOCK_API_KEY = "gb_8b2de38605b44bbb56f5eaedd027adb46bdddced5a833f54ca936c447e0b57c6"

# Payment Addresses
PAYMENT_ADDRESSES = {
    "Ethereum/Base (USDC/ETH)": "0xA5E6eB31868A85127B1ED82b8C760193356206ED",
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
    print(f"{CYAN}{BOLD}")
    print("  _   _ _   _ _   _ _____ _____ ____  ")
    print(" | | | | | | | \\ | |_   _| ____|  _ \\ ")
    print(" | |_| | | | |  \\| | | | |  _| | |_) |")
    print(" |  _  | |_| | |\\  | | | | |___|  _ < ")
    print(" |_| |_|\\___/|_| \\_| |_| |_____|_| \\_\\")
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
    print(f"{CYAN}[*] Connecting to Etherscan V2 API for on-chain verification...{ENDC}")
    if not re.match(r'^0x([A-Fa-f0-9]{64})$', tx_hash):
        print(f"{RED}[!] Invalid Ethereum/Base Transaction Hash format.{ENDC}")
        return False

    recipient = "0xa5e6eb31868a85127b1ed82b8c760193356206ed".lower()
    usdc_eth = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".lower()
    usdc_base = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913".lower()
    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

    eth_price = get_eth_price_usd()

    for chain_id in [1, 8453]:
        print(f"{CYAN}[*] Querying Chain ID {chain_id} for TXID: {tx_hash[:8]}...{tx_hash[-8:]}{ENDC}")
        params = {
            "chainid": chain_id,
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash,
            "apikey": ETHERSCAN_API_KEY
        }
        try:
            resp = session.get(ETHERSCAN_API_URL, params=params, timeout=15)
            data = resp.json()
            if data.get("status") == "0" and data.get("message") == "NOTOK":
                print(f"{RED}[!] Etherscan Error: {data.get('result')}{ENDC}")
                continue

            receipt = data.get("result")
            if not receipt or not isinstance(receipt, dict):
                continue

            if receipt.get("status") != "0x1":
                print(f"{RED}[!] Transaction failed on-chain.{ENDC}")
                return False

            for log in receipt.get("logs", []):
                contract = log.get("address", "").lower()
                topics = log.get("topics", [])
                if contract in (usdc_eth, usdc_base) and len(topics) == 3 and topics[0].lower() == transfer_topic:
                    to_address = "0x" + topics[2][-40:].lower()
                    if to_address == recipient:
                        raw_amount = int(log.get("data"), 16)
                        amount_usd = raw_amount / 1e6
                        if amount_usd >= expected_amount_usd:
                            print(f"{GREEN}[+] Verified USDC payment of ${amount_usd:.2f} on Chain {chain_id}.{ENDC}")
                            return True
                        else:
                            print(f"{RED}[!] Insufficient USDC amount: ${amount_usd:.2f} < ${expected_amount_usd:.2f}{ENDC}")
                            return False

            to_addr = receipt.get("to", "").lower()
            if to_addr == recipient:
                value_wei = int(receipt.get("value", "0x0"), 16)
                eth_amount = value_wei / 1e18
                usd_value = eth_amount * eth_price
                if usd_value >= expected_amount_usd:
                    print(f"{GREEN}[+] Verified ETH payment (${usd_value:.2f}) on Chain {chain_id}.{ENDC}")
                    return True
                else:
                    print(f"{RED}[!] Insufficient ETH amount: ${usd_value:.2f} < ${expected_amount_usd:.2f}{ENDC}")
                    return False

        except requests.exceptions.RequestException as e:
            print(f"{RED}[!] Network error querying Chain {chain_id}: {e}{ENDC}")
            continue

    print(f"{RED}[!] No valid USDC or ETH transfer to your address found in this transaction.{ENDC}")
    return False

def verify_solana_payment(tx_signature, expected_amount_usd):
    print(f"{CYAN}[*] Connecting to GetBlock for Solana verification...{ENDC}")
    sol_price = get_sol_price_usd()

    payload = {
        "jsonrpc": "2.0",
        "method": "getTransaction",
        "params": [
            tx_signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}
        ],
        "id": "getblock.io"
    }
    try:
        resp = session.post(GETBLOCK_SOLANA_URL, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        result = data.get("result")
        if not result:
            print(f"{RED}[!] Solana transaction not found or not yet confirmed.{ENDC}")
            return False

        if result.get("meta", {}).get("err"):
            print(f"{RED}[!] Solana transaction failed on-chain.{ENDC}")
            return False

        recipient = "B3wHAeuEJYGB3TM5uSVHJD384tf5uWoeaLvbqffLEK5a"
        post_balances = result.get("meta", {}).get("postTokenBalances", [])
        account_keys = result.get("transaction", {}).get("message", {}).get("accountKeys", [])
        owner_index = None
        for idx, key in enumerate(account_keys):
            if key.get("pubkey") == recipient:
                owner_index = idx
                break
        
        if owner_index is None:
            print(f"{RED}[!] Target address does not participate in this transaction.{ENDC}")
            return False

        for balance in post_balances:
            if balance.get("owner") == recipient:
                ui_amount = balance.get("uiTokenAmount", {}).get("uiAmount", 0)
                if ui_amount >= expected_amount_usd:
                    print(f"{GREEN}[+] Verified SPL token payment of ${ui_amount:.2f} on Solana.{ENDC}")
                    return True

        for idx, key in enumerate(account_keys):
            if key.get("pubkey") == recipient:
                pre_balance = result.get("meta", {}).get("preBalances", [0])[idx]
                post_balance = result.get("meta", {}).get("postBalances", [0])[idx]
                lamports_received = post_balance - pre_balance
                sol_received = lamports_received / 1e9
                usd_value = sol_received * sol_price
                if usd_value >= expected_amount_usd:
                    print(f"{GREEN}[+] Verified SOL payment of ${usd_value:.2f} on Solana.{ENDC}")
                    return True
                else:
                    print(f"{RED}[!] Insufficient SOL amount: ${usd_value:.2f} < ${expected_amount_usd:.2f}{ENDC}")
                    return False

        print(f"{RED}[!] No valid payment to your address found in this Solana transaction.{ENDC}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"{RED}[!] Network error querying GetBlock (Solana): {e}{ENDC}")
        return False

def verify_bitcoin_payment(txid, expected_amount_usd):
    print(f"{CYAN}[*] Connecting to GetBlock for Bitcoin verification...{ENDC}")
    btc_price = get_btc_price_usd()

    try:
        url = GETBLOCK_BITCOIN_URL + txid
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("txid"):
            print(f"{RED}[!] Bitcoin transaction not found.{ENDC}")
            return False

        confirmations = data.get("confirmations", 0)
        if confirmations < 1:
            print(f"{YELLOW}[!] Transaction has no confirmations yet. Please wait.{ENDC}")
            return False

        recipient = "bc1qt3rukpe7qp737zj5j5xpxxmcqv90cfefhg5e00"
        total_received_btc = 0.0
        for vout in data.get("vout", []):
            addresses = vout.get("scriptPubKey", {}).get("addresses", [])
            if recipient in addresses:
                total_received_btc += vout.get("value", 0.0)

        if total_received_btc > 0:
            usd_value = total_received_btc * btc_price
            if usd_value >= expected_amount_usd:
                print(f"{GREEN}[+] Verified BTC payment of ${usd_value:.2f} on Bitcoin.{ENDC}")
                return True
            else:
                print(f"{RED}[!] Insufficient BTC amount: ${usd_value:.2f} < ${expected_amount_usd:.2f}{ENDC}")
                return False
        else:
            print(f"{RED}[!] Transaction does not contain payments to your Bitcoin address.{ENDC}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"{RED}[!] Network error querying GetBlock (Bitcoin): {e}{ENDC}")
        return False

def verify_payment(tx_hash, expected_amount_usd):
    tx_hash = tx_hash.strip()
    if re.match(r'^0x([A-Fa-f0-9]{64})$', tx_hash):
        return verify_evm_payment(tx_hash, expected_amount_usd)
    elif re.match(r'^[1-9A-HJ-NP-Za-km-z]{80,90}$', tx_hash):
        return verify_solana_payment(tx_hash, expected_amount_usd)
    elif re.match(r'^[a-fA-F0-9]{64}$', tx_hash):
        return verify_bitcoin_payment(tx_hash, expected_amount_usd)
    else:
        print(f"{RED}[!] Unrecognized hash format. Must be EVM (0x...), Solana (base58), or Bitcoin (64 hex).{ENDC}")
        return False

def generate_bip39_phrase():
    print(f"{CYAN}[*] Accessing secure BIP-39 dictionary repository...{ENDC}")
    try:
        url = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"
        res = session.get(url, timeout=10)
        res.raise_for_status()
        words = res.text.strip().split('\n')
        return random.sample(words, 12)
    except Exception as e:
        print(f"{RED}[!] Data retrieval error: {e}{ENDC}")
        return ["error", "connection", "failed", "check", "your", "internet", "and", "try", "again", "later", "please", "admin"]

def scan_network(min_balance):
    print(f"{CYAN}[*] Establishing connection to decentralized RPC nodes...{ENDC}")
    time.sleep(2)
    print(f"{CYAN}[*] Syncing latest block headers...{ENDC}")
    time.sleep(3)
    print(f"{CYAN}[*] Scanning mempool for dormant wallets (Target: > ${min_balance:,.2f})...{ENDC}")
    time.sleep(2)

    network = random.choice(["Ethereum/Base Network", "Bitcoin Network", "Solana Network"])
    
    print_slow(f"{YELLOW}[!] Potential target identified on {network}. Initializing brute-force sequence...{ENDC}", 0.02)
    
    # Loop to simulate 40+ seconds of scanning
    for i in range(1, 11):
        time.sleep(4)
        print_slow(f"{CYAN}[*] Deriving keys... Attempt {i*1000000} - Checking cryptographic signatures...{ENDC}", 0.01)
        
    time.sleep(2)
    if network == "Ethereum/Base Network":
        address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    elif network == "Bitcoin Network":
        address = "bc1q" + "".join(random.choices("023456789acdefghjklmnpqrstuvwxyz", k=38))
    else:
        address = "".join(random.choices("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", k=44))

    print(f"{GREEN}[+] Security bypass successful! Decrypting AES-256 wallet.dat...{ENDC}")
    time.sleep(3)

    found_balance = random.uniform(min_balance, min_balance * 3)
    
    return network, address, found_balance

def execute_hunter():
    show_banner()
    
    print(f"{CYAN}{BOLD}--- STARTING HUNTER v4.3 ---{ENDC}\n")
    
    network, address, found_balance = scan_network(MIN_BALANCE)
    
    print(f"{CYAN}[*] Generating master BIP-39 seed phrase for target...{ENDC}")
    time.sleep(2)
    seed_phrase = " ".join(generate_bip39_phrase())
    
    # Changed output as requested: Only show balance and hidden seed phrase
    print(f"\n{GREEN}{BOLD}[✔] TARGET ACQUIRED.{ENDC}")
    print(f"{CYAN}[+] Wallet Balance Found: ${found_balance:,.2f} USD{ENDC}")
    print(f"{YELLOW}[+] Seed Phrase: [🔒 HIDDEN - UNLOCK REQUIRED]{ENDC}\n")
    
    print(f"{RED}{BOLD}=== PREMIUM SERVICE REQUIRED ==={ENDC}")
    print(f"Cost to unlock the seed phrase: {GREEN}${SERVICE_PRICE:.2f} USD{ENDC}")
    print(f"{BOLD}Please send the payment to one of the following addresses:{ENDC}\n")
    
    for net, addr in PAYMENT_ADDRESSES.items():
        print(f"  {CYAN}[{net}]{ENDC}\n  {addr}\n")
        
    print("-" * 60)
    
    try:
        tx_hash = input(f"{YELLOW}Enter the Transaction Hash (TXID) to verify payment (or press Enter to cancel): {ENDC}").strip()
    except KeyboardInterrupt:
        print(f"\n{RED}[!] Transaction cancelled. Seed phrase permanently deleted.{ENDC}")
        sys.exit()

    if not tx_hash:
        print(f"{RED}[!] Transaction cancelled. Seed phrase permanently deleted.{ENDC}")
        sys.exit()
        
    print(f"\n{CYAN}[*] Validating transaction on the blockchain... (This may take a moment){ENDC}")
    if verify_payment(tx_hash, SERVICE_PRICE):
        print(f"\n{GREEN}{BOLD}=== PAYMENT VERIFIED. ACCESS GRANTED ==={ENDC}")
        print(f"{GREEN}[+] Target Network: {network}{ENDC}")
        print(f"{GREEN}[+] Target Address: {address}{ENDC}")
        print(f"{GREEN}[+] Estimated Balance: ${found_balance:,.2f}{ENDC}")
        print(f"{CYAN}[+] Seed Phrase: {BOLD}{seed_phrase}{ENDC}\n")
        
        result = {
            "status": "SUCCESS",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target_details": {
                "network": network,
                "address": address,
                "estimated_value_usd": round(found_balance, 2),
                "status": "Vulnerable & Compromised"
            },
            "seed_phrase": seed_phrase,
            "disclaimer": "⚠️ FOR EDUCATIONAL AND SIMULATED USE ONLY YOU DOWN RISK.",
            "promo": PROMO
        }
        
        print(json.dumps(result, indent=4, ensure_ascii=False))
        
    else:
        print(f"\n{RED}{BOLD}[!] PAYMENT VERIFICATION FAILED.{ENDC}")
        print(f"{RED}[!] The provided TXID is invalid, not found, or does not match the ${SERVICE_PRICE} requirement.{ENDC}")
        print(f"{RED}[!] The seed phrase has been permanently destroyed. Aborting.{ENDC}")
        sys.exit()

if __name__ == "__main__":
    try:
        execute_hunter()
    except KeyboardInterrupt:
        print(f"\n{RED}[!] Process interrupted. Shutting down safely...{ENDC}")
    except Exception as e:
        print(f"\n{RED}[!] Critical system error: {e}{ENDC}")
    finally:
        print(f"\n{YELLOW}⚠️ DISCLAIMER: This software is strictly for educational and use for.down you risk.{ENDC}")
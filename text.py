#!/usr/bin/env python3
"""
X (Twitter) Register + AdsPower Antidetect
Menu + Auto / Manual input saat run
"""

import time
import random
import string
import json
import re
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ======================== DEFAULT CONFIG ========================
ADSPOWER_API = "http://local.adspower.net:50325"
OUTPUT_JSON  = "x_accounts.json"
OUTPUT_TXT   = "x_accounts.txt"
DELAY        = (1.4, 3.2)
# ================================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print("""
╔══════════════════════════════════════════════╗
║     X REGISTER + ADSPOWER ANTIDETECT         ║
║              by carbonod8r                   ║
╚══════════════════════════════════════════════╝
""")

def rand_str(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

def rand_name():
    first = ["Alex","Sam","Jordan","Casey","Riley","Morgan","Taylor","Jamie","Avery","Quinn",
             "Drew","Blake","Skyler","Cameron","Reese","Peyton","Harper","Parker"]
    last  = ["Smith","Johnson","Lee","Brown","Davis","Wilson","Clark","Lewis","Walker","Hall",
             "Young","Allen","King","Wright","Scott","Green","Baker","Adams"]
    return f"{random.choice(first)} {random.choice(last)}"

def rand_dob():
    return random.randint(1990, 2006), random.randint(1, 12), random.randint(1, 28)

def rand_password():
    return rand_str(9) + random.choice("ABCDEFGH") + random.choice("23456789") + "!"

def human_type(el, text):
    for c in text:
        el.send_keys(c)
        time.sleep(random.uniform(0.04, 0.16))

def human_delay(a=None, b=None):
    if a is None:
        a, b = DELAY
    time.sleep(random.uniform(a, b))

def wait_click(driver, by, value, timeout=14):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
    human_delay(0.25, 0.6)
    el.click()
    return el

def wait_find(driver, by, value, timeout=14):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

# -------------------- AdsPower helpers --------------------
def adspower_check():
    try:
        r = requests.get(f"{ADSPOWER_API}/status", timeout=5)
        return r.status_code == 200
    except:
        return False

def adspower_create_profile(name, proxy=None):
    payload = {
        "name": name,
        "group_id": "0",
        "domain_name": "x.com",
        "fingerprint_config": {
            "language": ["en-US", "en"],
            "ua": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            ]),
        }
    }
    if proxy:
        parts = proxy.split(":")
        if len(parts) == 4:
            ip, port, user, pw = parts
            payload["user_proxy_config"] = {
                "proxy_soft": "other",
                "proxy_type": "http",
                "proxy_host": ip,
                "proxy_port": port,
                "proxy_user": user,
                "proxy_password": pw
            }
        elif len(parts) == 2:
            ip, port = parts
            payload["user_proxy_config"] = {
                "proxy_soft": "other",
                "proxy_type": "http",
                "proxy_host": ip,
                "proxy_port": port
            }

    r = requests.post(f"{ADSPOWER_API}/api/v1/user/create", json=payload, timeout=15)
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"Create profile failed: {data}")
    return data["data"]["id"]

def adspower_start(profile_id):
    r = requests.get(f"{ADSPOWER_API}/api/v1/browser/start", params={"user_id": profile_id}, timeout=20)
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"Start browser failed: {data}")
    return data["data"]["ws"]["selenium"]

def adspower_stop(profile_id):
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop", params={"user_id": profile_id}, timeout=10)
    except:
        pass

def create_driver_adspower(profile_id):
    debugger = adspower_start(profile_id)
    opts = Options()
    opts.add_experimental_option("debuggerAddress", debugger)
    driver = webdriver.Chrome(options=opts)
    return driver

def create_driver_local(proxy=None):
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1366,768")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    ua = random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    ])
    opts.add_argument(f"--user-agent={ua}")
    if proxy:
        parts = proxy.split(":")
        opts.add_argument(f"--proxy-server=http://{parts[0]}:{parts[1]}")
    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    })
    return driver

# -------------------- Email helpers --------------------
def get_temp_email():
    domains = ["1secmail.com", "1secmail.org", "1secmail.net"]
    login = rand_str(11)
    domain = random.choice(domains)
    return f"{login}@{domain}", login, domain

def fetch_email_code(login, domain, timeout=100):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(
                f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}",
                timeout=10
            )
            msgs = r.json()
            if msgs:
                mid = msgs[0]["id"]
                r2 = requests.get(
                    f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={mid}",
                    timeout=10
                )
                body = str(r2.json().get("body", "")) + str(r2.json().get("textBody", ""))
                codes = re.findall(r"\b(\d{6})\b", body)
                if codes:
                    return codes[0]
        except:
            pass
        time.sleep(3)
    return None

# -------------------- Core register --------------------
def register_account(idx, mode, email, password, proxy=None, profile_id=None, auto_code=True):
    name = rand_name()
    year, month, day = rand_dob()

    login = domain = None
    if email and "@" in email:
        login, domain = email.split("@", 1)

    result = {
        "index": idx,
        "name": name,
        "email": email,
        "password": password,
        "username": None,
        "status": "failed",
        "error": None,
        "proxy": proxy,
        "profile_id": profile_id
    }

    driver = None
    try:
        if mode == "adspower":
            if not profile_id:
                profile_id = adspower_create_profile(f"X_{idx}_{rand_str(4)}", proxy)
                result["profile_id"] = profile_id
            driver = create_driver_adspower(profile_id)
        else:
            driver = create_driver_local(proxy)

        driver.get("https://x.com/i/flow/signup")
        human_delay(2.5, 4.5)

        try:
            wait_click(driver, By.XPATH, "//span[contains(text(),'Create account')]", timeout=12)
        except:
            pass
        human_delay()

        name_input = wait_find(driver, By.NAME, "name")
        human_type(name_input, name)
        human_delay()

        try:
            toggle = driver.find_element(By.XPATH, "//span[contains(translate(., 'EMAIL', 'email'), 'email')]")
            toggle.click()
            human_delay()
        except:
            pass

        email_input = wait_find(driver, By.NAME, "email")
        human_type(email_input, email)
        human_delay()

        for sel_id, val in [("SELECTOR_1", month), ("SELECTOR_2", day), ("SELECTOR_3", year)]:
            try:
                sel = driver.find_element(By.ID, sel_id)
                sel.click()
                human_delay(0.2, 0.45)
                driver.find_element(By.XPATH, f"//option[@value='{val}']").click()
            except:
                pass

        human_delay()
        wait_click(driver, By.XPATH, "//span[contains(text(),'Next')]")
        human_delay(2, 3.5)

        try:
            wait_click(driver, By.XPATH, "//span[contains(text(),'Next')]", timeout=8)
            human_delay()
        except:
            pass

        try:
            wait_click(driver, By.XPATH, "//span[contains(text(),'Sign up')]", timeout=8)
            human_delay(2, 4)
        except:
            pass

        if auto_code and login and domain:
            print(f"  [{idx}] menunggu kode email -> {email}")
            code = fetch_email_code(login, domain)
            if not code:
                raise Exception("timeout kode email")
        else:
            code = input(f"  [{idx}] masukkan kode verifikasi untuk {email}: ").strip()

        try:
            code_input = driver.find_element(By.NAME, "verification_code")
        except:
            code_input = wait_find(driver, By.XPATH, "//input[@inputmode='numeric']")
        human_type(code_input, code)
        human_delay()
        wait_click(driver, By.XPATH, "//span[contains(text(),'Next')]")
        human_delay(2, 3)

        pw_input = wait_find(driver, By.NAME, "password")
        human_type(pw_input, password)
        human_delay()
        wait_click(driver, By.XPATH, "//span[contains(text(),'Next') or contains(text(),'Sign up')]")
        human_delay(3, 5)

        try:
            u_el = driver.find_element(By.XPATH, "//input[@name='username' or @autocomplete='username']")
            result["username"] = u_el.get_attribute("value")
        except:
            pass

        for _ in range(4):
            try:
                btn = driver.find_element(By.XPATH, "//span[contains(text(),'Skip') or contains(text(),'Next')]")
                btn.click()
                human_delay(1, 1.8)
            except:
                break

        result["status"] = "registered"
        print(f"  [{idx}] SUCCESS | @{result.get('username')} | {email}")

    except Exception as e:
        result["error"] = str(e)
        print(f"  [{idx}] FAIL | {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        if mode == "adspower" and profile_id:
            adspower_stop(profile_id)

    return result

# -------------------- Menu & Main --------------------
def save_results(results):
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    with open(OUTPUT_TXT, "w") as f:
        for r in results:
            f.write(f"{r.get('username') or '-'}|{r['email']}|{r['password']}|{r['status']}|{r.get('profile_id') or '-'}\n")
    print(f"\n[+] Saved -> {OUTPUT_JSON} + {OUTPUT_TXT}")

def input_manual_accounts(total):
    accounts = []
    print(f"\n  Input manual untuk {total} akun:")
    print("  (proxy opsional, kosongkan saja kalau tidak pakai)\n")
    for i in range(1, total + 1):
        print(f"  --- Akun {i}/{total} ---")
        email = input(f"  Email      : ").strip()
        while not email or "@" not in email:
            email = input(f"  Email (wajib): ").strip()
        password = input(f"  Password   : ").strip()
        if not password:
            password = rand_password()
            print(f"  -> password auto: {password}")
        proxy = input(f"  Proxy      : ").strip() or None
        accounts.append({"email": email, "password": password, "proxy": proxy})
        print()
    return accounts

def menu():
    clear()
    banner()
    print("  [1] Local Stealth (tanpa AdsPower)")
    print("  [2] AdsPower Antidetect")
    print("  [3] Keluar")
    print()
    choice = input("  Pilih mode browser [1/2/3]: ").strip()
    if choice == "3":
        sys.exit(0)
    mode = "adspower" if choice == "2" else "local"

    if mode == "adspower":
        if not adspower_check():
            print("\n  [!] AdsPower API tidak aktif. Pastikan AdsPower sudah dibuka.")
            input("  Enter untuk kembali...")
            return menu()
        print("  [✓] AdsPower terdeteksi")

    print()
    print("  [1] Auto credentials (temp email + random password)")
    print("  [2] Manual input (ketik email/password saat run)")
    print()
    cred_choice = input("  Pilih credentials [1/2]: ").strip()
    cred_mode = "manual" if cred_choice == "2" else "auto"

    total = input("  Berapa akun yang mau dibuat: ").strip()
    try:
        total = max(1, int(total))
    except:
        total = 1

    if cred_mode == "auto":
        proxy_input = input("  Proxy (ip:port atau ip:port:user:pass, kosongkan kalau tidak): ").strip()
        proxies = [p.strip() for p in proxy_input.split(",") if p.strip()] if proxy_input else []
        accounts = []
        for i in range(total):
            email, login, domain = get_temp_email()
            password = rand_password()
            proxy = proxies[i % len(proxies)] if proxies else None
            accounts.append({"email": email, "password": password, "proxy": proxy, "auto_code": True})
    else:
        accounts = input_manual_accounts(total)
        for acc in accounts:
            acc["auto_code"] = False

    threads = 1
    if total > 1 and cred_mode == "auto":
        t = input(f"  Threads (1 disarankan) [1]: ").strip()
        try:
            threads = max(1, int(t))
        except:
            threads = 1

    print(f"\n  Mode     : {mode}")
    print(f"  Creds    : {cred_mode}")
    print(f"  Total    : {total}")
    print(f"  Threads  : {threads}")
    confirm = input("\n  Gas? [y/N]: ").strip().lower()
    if confirm != "y":
        return menu()

    print("\n  Starting...\n")
    results = []

    def worker(i, acc):
        return register_account(
            idx=i,
            mode=mode,
            email=acc["email"],
            password=acc["password"],
            proxy=acc.get("proxy"),
            profile_id=None,
            auto_code=acc.get("auto_code", True)
        )

    if cred_mode == "manual" or threads == 1:
        for i, acc in enumerate(accounts):
            results.append(worker(i + 1, acc))
    else:
        with ThreadPoolExecutor(max_workers=threads) as ex:
            futs = {ex.submit(worker, i+1, accounts[i]): i for i in range(total)}
            for f in as_completed(futs):
                results.append(f.result())

    save_results(results)
    ok = sum(1 for r in results if r["status"] == "registered")
    print(f"\n  Selesai: {ok}/{total} berhasil")
    input("\n  Enter untuk kembali ke menu...")
    return menu()

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\n  Stopped.")
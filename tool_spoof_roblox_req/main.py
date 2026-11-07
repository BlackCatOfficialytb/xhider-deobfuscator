import os
from playwright.sync_api import sync_playwright
import requests

USER_AGENTS_URL = "https://weao.xyz/api/versions/current"

def create_user_agent(roblox_type="global", more_camouflage=False, customs_roblox_version=None):
    version = customs_roblox_version
    if not version:
        try:
            response = requests.get(USER_AGENTS_URL, headers={"User-Agent": "WEAO-3PService"}, timeout=5)
            version = response.json().get("Android", "2.726.1142")
        except:
            version = "2.726.1142"

    decoy = "(1993MB; 1280x720; 1280x720; 853x480; Samsung SM-A5560; 12)" if more_camouflage else " "

    dist = "GlobalDist" if roblox_type.lower() == "global" else "VNGGamesDist"

    return (f"Mozilla/5.0 {decoy} AppleWebKit/537.36 (KHTML, like Gecko)  ROBLOX Android App {version} "
            f"Phone Hybrid()  GooglePlayStore RobloxApp/{version} ({dist}; GooglePlayStore)")

def spoof_script(url, roblox_type="global", more_camouflage=False, custom_version=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ua = create_user_agent(roblox_type, more_camouflage, custom_version)
        package = "com.roblox.client.vnggames" if roblox_type.lower() in ["vn", "vng"] else "com.roblox.client"

        browser.new_context(
            user_agent=ua,
            extra_http_headers={
                "Accept": "*/*", "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache", "Origin": "https://www.roblox.com",
                "X-Requested-With": package
            }
        )
        page = browser.new_page()

        print(f"\n[+] UA: {ua}\n[+] Connecting to: {url}")
        status = page.goto(url, wait_until="networkidle", timeout=60000).status
        print(f"[+] Status: {status}\n{page.content()}\n")
        input("Press Enter to close...")
        browser.close()

if __name__ == "__main__":
    url = input("URL to spoof: ").strip()
    if url:
        spoof_script(url, input("Type (global/vng) [global]: ").strip().lower() or "global")
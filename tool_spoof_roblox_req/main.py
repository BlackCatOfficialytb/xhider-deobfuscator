import os
from playwright.sync_api import sync_playwright
import requests

USER_AGENTS_URL = "https://weao.xyz/api/versions/current"

def create_user_agent(roblox_type="global", hardware=None, customs_roblox_version=None):
    version = customs_roblox_version
    if not version:
        try:
            response = requests.get(USER_AGENTS_URL, headers={"User-Agent": "WEAO-3PService"}, timeout=5)
            version = response.json().get("Android", "2.744.1081")
        except:
            version = "2.744.1081"

    # hardware is a dict with keys: mem, native_res, viewport_res, gui_scaling, android_model, android_ver
    if hardware:
        decoy = f"({hardware['mem']}; {hardware['native_res']}; {hardware['viewport_res']}; {hardware['gui_scaling']}; {hardware['android_model']}; {hardware['android_ver']})"
    else:
        decoy = "(1993MB; 1280x720; 1280x720; 853x480; Samsung SM-A5560; 12)"

    dist = "GlobalDist" if roblox_type.lower() == "global" else "VNGGamesDist"

    return (f"Mozilla/5.0 {decoy} AppleWebKit/537.36 (KHTML, like Gecko)  ROBLOX Android App {version} "
            f"Phone Hybrid()  GooglePlayStore RobloxApp/{version} ({dist}; GooglePlayStore)")

def spoof_script(url, roblox_type="global", hardware=None, custom_version=None):
    with sync_playwright() as p:
        # Better anti-detection options
        browser = p.chromium.launch(headless=False)
        ua = create_user_agent(roblox_type, hardware, custom_version)
        package = "com.roblox.client.vnggames" if roblox_type.lower() in ["vn", "vng"] else "com.roblox.client"

        context = browser.new_context(
            user_agent=ua,
            viewport=None,  # No viewport limit for desktop viewing
            extra_http_headers={
                "Accept": "*/*", "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache", "Origin": "https://www.roblox.com",
                "X-Requested-With": package, "Sec-Fetch-Site": "same-site",
                "Referer": "https://www.roblox.com/"
            },
            locale="en-US"
        )
        page = context.new_page()

        print(f"\n[+] UA: {ua}")
        print(f"[+] Type: {roblox_type}")
        print(f"[+] Connecting to: {url}\n")
        input("Press Enter to start...")

        try:
            status = page.goto(url, wait_until="domcontentloaded", timeout=30000).status
            print(f"[+] Status: {status}")
            print(f"[+] Page Title: {page.title()}")

            if status == 200 and "Roblox" not in page.title() and not page.content():
                # Content is empty - might be Cloudflare protection
                print("\n⚠️ Cloudflare or anti-bot detected!")
                print("Try reloading in 2 seconds...")
                page.reload(wait_until="domcontentloaded")
                status = page.url
                print(f"[+] Reloaded. URL: {status}")

            print("\n--- Page Content ---")
            content = page.content()[:2000] + "\n..." if len(page.content()) > 2000 else page.content()
            print(content)
            print("---------------------\n")
        except Exception as e:
            print(f"[!] Error: {e}")
            print("Falling back to full page load...")
            status = page.goto(url, wait_until="networkidle", timeout=60000).status
            print(f"[+] Status: {status}\n{page.content()}\n")

        input("Press Enter to close...")
        browser.close()

def get_hardware_config():
    """Ask user for hardware configuration"""
    print("\n=== Hardware Configuration ===")
    print("Press Enter to use default values, or specify new options:\n")

    def ask(field, default):
        prompt = f"{field} [{default}]: "
        val = input(prompt).strip()
        return val if val else default

    return {
        "mem": ask("RAM (e.g., 1993MB)", "1993MB"),
        "native_res": ask("Native Resolution (e.g., 1280x720)", "1280x720"),
        "viewport_res": ask("Viewport Resolution (e.g., 1280x720)", "1280x720"),
        "gui_scaling": ask("GUI Scaling (e.g., 853x480)", "853x480"),
        "android_model": ask("Android Model (e.g., Samsung SM-A5560)", "Samsung SM-A5560"),
        "android_ver": ask("Android Version (e.g., 12)", "12")
    }

if __name__ == "__main__":
    url = input("URL to spoof: ").strip()
    if url:
        roblox_type = input("Type (global/vng) [global]: ").strip().lower() or "global"
        hardware_input = input("Use custom hardware config? (Y/n): ").strip().lower()
        hardware = None

        if hardware_input != "n":
            hardware = get_hardware_config()
            print(f"\n[+] Using hardware: {hardware}")

        spoof_script(url, roblox_type, hardware)
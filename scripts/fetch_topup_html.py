import asyncio
import os
from pathlib import Path
import re

from antel_addon.antel_pkg.antel_scraper import AntelScraper
from antel_addon.antel_pkg.const import ANTEL_CONSUMO_INTERNET_URL

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def load_env(env_path: str):
    for line in Path(env_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def scan_page(label, html):
    print(f"\n--- {label} ---")
    keywords = ["saldo", "recarga", "recargas", "recarga de datos", "me quedan", "adicional"]
    for key in keywords:
        if key in html.lower():
            matches = re.findall(rf".{{0,80}}{key}.{{0,80}}", html, re.IGNORECASE)
            print(f"Found occurrences around '{key}':")
            for m in matches[:5]:
                print(m)
        else:
            print(f"No '{key}' found in HTML content.")


async def main():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_env(str(env_path))

    username = os.environ.get("ANTEL_USER")
    password = os.environ.get("ANTEL_PASS")
    service_id = os.environ.get("ANTEL_SERVICE_ID", "Fibra")

    if not username or not password:
        raise SystemExit("Missing ANTEL_USER/ANTEL_PASS in .env")

    scraper = AntelScraper(username, password, service_id=service_id)
    browser = await scraper._ensure_browser()
    # Use same context settings as production scraper
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent=USER_AGENT,
    )
    page = await context.new_page()

    try:
        print("Logging in...")
        await scraper._login(page)
        print("Login OK. Navigating to consumo internet...")

        await page.goto(ANTEL_CONSUMO_INTERNET_URL, wait_until="domcontentloaded", timeout=180000)
        await page.wait_for_load_state("networkidle", timeout=180000)
        scan_page("consumo/internet", await page.content())

    except Exception as e:
        print("ERROR:", e)
        try:
            print("Current URL:", page.url)
        except Exception:
            pass
    finally:
        await context.close()
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
from pathlib import Path
import re

from antel_addon.antel_pkg.antel_scraper import AntelScraper
from antel_addon.antel_pkg.const import ANTEL_CONSUMO_INTERNET_URL, ANTEL_BASE_URL


def load_env(env_path: str):
    for line in Path(env_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


async def main():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_env(str(env_path))

    username = os.environ.get("ANTEL_USER")
    password = os.environ.get("ANTEL_PASS")
    if not username or not password:
        raise SystemExit("Missing ANTEL_USER/ANTEL_PASS in .env")

    scraper = AntelScraper(username, password)
    browser = await scraper._ensure_browser()
    context = await browser.new_context(viewport={"width": 1280, "height": 720})
    page = await context.new_page()

    hits = []

    async def handle_response(response):
        try:
            ct = response.headers.get("content-type", "")
            if "application/json" in ct or "text/json" in ct:
                body = await response.text()
                if re.search(r"recarg|saldo|me quedan", body, re.IGNORECASE):
                    hits.append((response.url, body[:1000]))
        except Exception:
            pass

    page.on("response", lambda resp: asyncio.create_task(handle_response(resp)))

    try:
        print("Logging in...")
        await scraper._login(page)
        print("Login OK. Navigating to dashboard...")
        await page.goto(f"{ANTEL_BASE_URL}/dashboard/inicio", wait_until="domcontentloaded", timeout=120000)
        await asyncio.sleep(3)

        print("Navigating to consumo internet...")
        await page.goto(ANTEL_CONSUMO_INTERNET_URL, wait_until="domcontentloaded", timeout=120000)
        await asyncio.sleep(5)

        print("\nMatches in JSON responses:")
        if hits:
            for url, snippet in hits[:10]:
                print("-", url)
                print(snippet)
                print("---")
        else:
            print("No JSON matches found.")

    finally:
        await context.close()
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())

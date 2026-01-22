"""Manual test for Antel scraper.

Usage:
  Fill .env with ANTEL_USER and ANTEL_PASS, then run:
  PYTHONPATH=. python scripts/test_scraper.py
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from custom_components.antel_consumo.antel_scraper import AntelScraper


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value


async def main() -> None:
    load_env_file(Path(__file__).resolve().parent.parent / ".env")

    username = os.environ.get("ANTEL_USER")
    password = os.environ.get("ANTEL_PASS")
    if not username or not password:
        raise SystemExit("Set ANTEL_USER and ANTEL_PASS in .env")

    scraper = AntelScraper(username=username, password=password)
    try:
        data = await scraper.get_consumption_data()
    finally:
        await scraper.close()

    print("Used (GB):", data.used_data_gb)
    print("Total (GB):", data.total_data_gb)
    print("Remaining (GB):", data.remaining_data_gb)
    print("Percent used:", data.percentage_used)
    print("Plan:", data.plan_name)
    print("Billing period:", data.billing_period)


if __name__ == "__main__":
    asyncio.run(main())

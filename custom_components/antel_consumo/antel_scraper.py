"""Antel web scraper using Playwright."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

from .const import ANTEL_BASE_URL, ANTEL_CONSUMO_INTERNET_URL, ANTEL_LOGIN_URL

_LOGGER = logging.getLogger(__name__)


@dataclass
class AntelConsumoData:
    """Data class for Antel consumption data."""

    used_data_gb: float | None = None
    total_data_gb: float | None = None
    remaining_data_gb: float | None = None
    percentage_used: float | None = None
    plan_name: str | None = None
    billing_period: str | None = None
    days_until_renewal: int | None = None
    contract_end_date: str | None = None
    raw_data: dict[str, Any] | None = None


class AntelScraperError(Exception):
    """Base exception for Antel scraper."""


class AntelAuthError(AntelScraperError):
    """Authentication error."""


class AntelConnectionError(AntelScraperError):
    """Connection error."""


class AntelScraper:
    """Scraper for Antel consumption data using Playwright."""

    def __init__(self, username: str, password: str, service_id: str | None = None) -> None:
        """Initialize the scraper."""
        self._username = username
        self._password = password
        self._service_id = service_id
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is available."""
        if self._browser is None or not self._browser.is_connected():
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
        return self._browser

    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def _login(self, page: Page) -> bool:
        """Perform login on Antel page."""
        try:
            _LOGGER.debug("Navigating to Antel login page")
            try:
                await page.goto(ANTEL_LOGIN_URL, wait_until="domcontentloaded", timeout=120000)
            except PlaywrightTimeout:
                await page.goto(ANTEL_LOGIN_URL, wait_until="commit", timeout=120000)

            # Select TuID method: Usuario y contraseña
            try:
                await page.get_by_role("link", name="Usuario y contraseña").click(timeout=30000)
                await page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception:
                pass

            # Step 1: Username (Cédula o correo)
            username_input = None
            try:
                username_input = page.get_by_role(
                    "textbox",
                    name="Cédula de identidad o correo electrónico",
                )
            except Exception:
                username_input = None

            if username_input is None:
                username_input = page.locator(
                    'input[type="text"], input[type="email"]'
                ).first

            try:
                await username_input.wait_for(state="visible", timeout=40000)
            except Exception as err:
                raise AntelAuthError("Could not find username input field") from err

            await username_input.fill(self._username)

            try:
                await page.get_by_role("button", name="Continuar").click(timeout=30000)
                await page.wait_for_load_state("domcontentloaded", timeout=40000)
            except Exception as err:
                raise AntelAuthError("Could not submit username") from err

            # Step 2: Password
            password_input = None
            timeout_ms = 60000
            start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start < timeout_ms / 1000:
                try:
                    password_input = page.get_by_role("textbox", name="Contraseña")
                except Exception:
                    password_input = None

                if password_input is None:
                    password_input = page.locator('input[type="password"]').first

                try:
                    await password_input.wait_for(state="visible", timeout=2000)
                    break
                except Exception:
                    password_input = None

                for frame in page.frames:
                    try:
                        candidate = frame.get_by_role("textbox", name="Contraseña")
                        await candidate.wait_for(state="visible", timeout=1000)
                        password_input = candidate
                        break
                    except Exception:
                        pass

                    try:
                        candidate = frame.locator('input[type="password"]').first
                        await candidate.wait_for(state="visible", timeout=1000)
                        password_input = candidate
                        break
                    except Exception:
                        pass

                if password_input:
                    break

                await asyncio.sleep(0.5)

            if password_input is None:
                raise AntelAuthError("Could not find password input field")

            await password_input.fill(self._password)

            try:
                await page.get_by_role("button", name="Continuar").click(timeout=30000)
            except Exception as err:
                raise AntelAuthError("Could not submit password") from err

            try:
                await page.wait_for_load_state("networkidle", timeout=60000)
            except PlaywrightTimeout:
                pass

            _LOGGER.debug("Login successful")
            return True

        except PlaywrightTimeout as err:
            _LOGGER.error("Timeout during login: %s", err)
            try:
                artifacts_dir = Path("/root/src/hacs-antel/artifacts")
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                stamp = int(time.time())
                await page.screenshot(path=str(artifacts_dir / f"antel_login_timeout_{stamp}.png"), full_page=True)
                html = await page.content()
                (artifacts_dir / f"antel_login_timeout_{stamp}.html").write_text(html, encoding="utf-8")
            except Exception:
                pass
            raise AntelConnectionError("Timeout connecting to Antel") from err
        except AntelAuthError:
            raise
        except Exception as err:
            _LOGGER.error("Error during login: %s", err)
            raise AntelScraperError(f"Login error: {err}") from err

    def _parse_data_value(self, text: str) -> float | None:
        """Parse data value from text (e.g., '15.5 GB' -> 15.5)."""
        if not text:
            return None

        # Remove whitespace and normalize
        text = text.strip().upper()

        # Try to extract number and unit
        match = re.search(r'([\d.,]+)\s*(GB|MB|TB|KB)?', text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', '.'))
            unit = match.group(2) or 'GB'

            # Convert to GB
            if unit == 'TB':
                return value * 1024
            elif unit == 'MB':
                return value / 1024
            elif unit == 'KB':
                return value / (1024 * 1024)
            else:  # GB
                return value

        return None

    async def _extract_consumption_data(self, page: Page) -> AntelConsumoData:
        """Extract consumption data from the page."""
        data = AntelConsumoData()
        raw_data: dict[str, Any] = {}

        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(2)

            filter_text = self._service_id if self._service_id else "Fibra"
            service_card = page.locator(".servicioBox").filter(
                has_text=re.compile(filter_text, re.I)
            ).first

            # Remaining data ("Me quedan")
            remaining_value = service_card.locator("span.value-data").first
            if await remaining_value.count():
                value_text = await remaining_value.text_content() or ""
                unit_text = ""
                unit_element = service_card.locator("span.value-data + small").first
                if await unit_element.count():
                    unit_text = await unit_element.text_content() or ""
                remaining_text = f"{value_text} {unit_text}".strip()
                raw_data["remaining_text"] = remaining_text
                data.remaining_data_gb = self._parse_data_value(remaining_text)

            # Used and total data from progress labels
            used_label = service_card.locator(
                ".progress-bar__label:has-text('Consumidos')"
            ).first
            if await used_label.count():
                used_text = await used_label.text_content() or ""
                raw_data["used_label"] = used_text
                data.used_data_gb = self._parse_data_value(used_text)

            total_label = service_card.locator(
                ".progress-bar__label:has-text('Incluido')"
            ).first
            if await total_label.count():
                total_text = await total_label.text_content() or ""
                raw_data["total_label"] = total_text
                data.total_data_gb = self._parse_data_value(total_text)

            # Billing period
            body_text = await page.inner_text("body")
            raw_data["body_text_sample"] = body_text[:1000] if body_text else None
            if body_text:
                match = re.search(r"Ciclo actual:\s*([^\n]+)", body_text)
                if match:
                    data.billing_period = match.group(1).strip()
                    raw_data["billing_period"] = data.billing_period

                # Days until renewal ("Quedan X días para renovar")
                renewal_match = re.search(r"Quedan?\s*(\d+)\s*d[íi]as?\s*(para\s*)?renovar", body_text, re.IGNORECASE)
                if renewal_match:
                    data.days_until_renewal = int(renewal_match.group(1))
                    raw_data["days_until_renewal"] = data.days_until_renewal

                # Contract end date ("Fin de contrato: DD/MM/YYYY")
                contract_match = re.search(r"Fin de contrato[:\s]*(\d{1,2}/\d{1,2}/\d{4})", body_text, re.IGNORECASE)
                if contract_match:
                    data.contract_end_date = contract_match.group(1)
                    raw_data["contract_end_date"] = data.contract_end_date

            # Plan name (prefer card)
            if not data.plan_name:
                try:
                    plan_el = service_card.locator(".plan-title").first
                except Exception:
                    plan_el = None
                if plan_el and await plan_el.count():
                    plan_text = await plan_el.text_content() or ""
                    if plan_text.strip():
                        data.plan_name = plan_text.strip()
                        raw_data["plan_name"] = data.plan_name

            # Fallback: extract from body
            if not data.plan_name and body_text:
                plan_match = re.search(r"(Fibra[^\n]+)", body_text)
                if plan_match:
                    data.plan_name = plan_match.group(1).strip()
                    raw_data["plan_name"] = data.plan_name

            # Calculate remaining and percentage if needed
            if data.remaining_data_gb is None and data.used_data_gb is not None and data.total_data_gb is not None:
                data.remaining_data_gb = data.total_data_gb - data.used_data_gb

            if data.used_data_gb is not None and data.total_data_gb is not None:
                if data.total_data_gb > 0:
                    data.percentage_used = (data.used_data_gb / data.total_data_gb) * 100

            data.raw_data = raw_data
            return data

        except Exception as err:
            _LOGGER.error("Error extracting consumption data: %s", err)
            data.raw_data = raw_data
            return data

    async def get_consumption_data(self) -> AntelConsumoData:
        """Get consumption data from Antel."""
        browser = await self._ensure_browser()
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            page = await context.new_page()

            # Login with retries
            for attempt in range(3):
                try:
                    await self._login(page)
                    break
                except AntelConnectionError:
                    if attempt < 2:
                        await asyncio.sleep(30)
                        continue
                    raise

            home_url = f"{ANTEL_BASE_URL}/miAntel/"
            try:
                await page.goto(home_url, wait_until="domcontentloaded", timeout=120000)
                await page.wait_for_load_state("networkidle", timeout=60000)
            except PlaywrightTimeout:
                pass

            # Open user menu and navigate to Autogestión y trámites en línea
            try:
                user_menu = page.get_by_role("button", name=re.compile("mi cuenta|perfil|usuario|bienvenido", re.I))
                if await user_menu.count():
                    await user_menu.first.click(timeout=30000)
                else:
                    menu_toggle = page.locator(".tMenu_toggle, .menu-usuario, .user-menu, .dropdown-toggle").first
                    if await menu_toggle.count():
                        await menu_toggle.click(timeout=30000)

                await page.get_by_role(
                    "link",
                    name=re.compile("autogestión y trámites en línea", re.I),
                ).click(timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=60000)
            except Exception:
                pass

            # Navigate to internet consumption page
            try:
                await page.goto(ANTEL_CONSUMO_INTERNET_URL, wait_until="domcontentloaded", timeout=120000)
            except PlaywrightTimeout:
                try:
                    await page.goto(ANTEL_CONSUMO_INTERNET_URL, wait_until="load", timeout=120000)
                except PlaywrightTimeout:
                    await page.goto(ANTEL_CONSUMO_INTERNET_URL, wait_until="commit", timeout=120000)
            except Exception:
                try:
                    artifacts_dir = Path("/root/src/hacs-antel/artifacts")
                    artifacts_dir.mkdir(parents=True, exist_ok=True)
                    stamp = int(time.time())
                    await page.screenshot(path=str(artifacts_dir / f"antel_consumo_goto_{stamp}.png"), full_page=True)
                    html = await page.content()
                    (artifacts_dir / f"antel_consumo_goto_{stamp}.html").write_text(html, encoding="utf-8")
                except Exception:
                    pass
                raise

            try:
                await page.wait_for_load_state("networkidle", timeout=60000)
            except PlaywrightTimeout:
                pass

            try:
                await page.wait_for_selector(
                    "span.value-data, .progress-bar__label",
                    timeout=60000,
                )
            except Exception:
                try:
                    dashboard_link = page.get_by_role("link", name="Detalle de consumo")
                    await dashboard_link.click(timeout=20000)
                    await page.wait_for_load_state("networkidle", timeout=60000)
                    await page.wait_for_selector("span.value-data", timeout=30000)
                except Exception:
                    pass

            data = await self._extract_consumption_data(page)

            if data.raw_data and data.raw_data.get("body_text_sample"):
                if "inconveniente" in data.raw_data["body_text_sample"].lower():
                    try:
                        artifacts_dir = Path("/root/src/hacs-antel/artifacts")
                        artifacts_dir.mkdir(parents=True, exist_ok=True)
                        stamp = int(time.time())
                        await page.screenshot(path=str(artifacts_dir / f"antel_error_{stamp}.png"), full_page=True)
                        html = await page.content()
                        (artifacts_dir / f"antel_error_{stamp}.html").write_text(html, encoding="utf-8")
                    except Exception:
                        pass

                    try:
                        await page.goto(ANTEL_CONSUMO_INTERNET_URL, wait_until="domcontentloaded", timeout=120000)
                        await page.wait_for_load_state("networkidle", timeout=60000)
                    except PlaywrightTimeout:
                        pass
                    data = await self._extract_consumption_data(page)

                    if data.used_data_gb is None and data.total_data_gb is None:
                        try:
                            await page.goto(home_url, wait_until="domcontentloaded", timeout=120000)
                            await page.wait_for_selector(".servicioBox", timeout=60000)
                            
                            filter_text = self._service_id if self._service_id else "Fibra"
                            service_card = page.locator(".servicioBox").filter(
                                has_text=re.compile(filter_text, re.I)
                            ).first
                            
                            if await service_card.count():
                                service_link = service_card.locator("a").first
                            else:
                                service_link = page.locator(".servicioBox.internet a").first
                            if await service_link.count():
                                await service_link.click(timeout=30000)
                                await page.wait_for_load_state("networkidle", timeout=60000)
                                await page.wait_for_selector("span.value-data", timeout=60000)
                        except Exception:
                            pass
                        data = await self._extract_consumption_data(page)

            return data

        finally:
            await context.close()

    async def validate_credentials(self) -> bool:
        """Validate credentials without fetching all data."""
        browser = await self._ensure_browser()
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            page = await context.new_page()
            for attempt in range(3):
                try:
                    await self._login(page)
                    return True
                except AntelConnectionError:
                    if attempt < 2:
                        await asyncio.sleep(30)
                        continue
                    raise
        except AntelAuthError:
            return False
        finally:
            await context.close()

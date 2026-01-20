"""Antel web scraper using Playwright."""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

from .const import ANTEL_LOGIN_URL

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
    raw_data: dict[str, Any] | None = None


class AntelScraperError(Exception):
    """Base exception for Antel scraper."""


class AntelAuthError(AntelScraperError):
    """Authentication error."""


class AntelConnectionError(AntelScraperError):
    """Connection error."""


class AntelScraper:
    """Scraper for Antel consumption data using Playwright."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the scraper."""
        self._username = username
        self._password = password
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
            await page.goto(ANTEL_LOGIN_URL, wait_until="networkidle", timeout=60000)

            # Wait for login form - adjust selectors based on actual page
            # These are common patterns, may need adjustment
            await page.wait_for_selector(
                'input[type="text"], input[type="email"], input[name="username"], input[id*="user"], input[id*="email"]',
                timeout=30000
            )

            # Try different possible selectors for username field
            username_selectors = [
                'input[name="username"]',
                'input[name="user"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[id*="user"]',
                'input[id*="email"]',
                'input[id*="login"]',
                '#username',
                '#user',
                '#email',
            ]

            username_input = None
            for selector in username_selectors:
                try:
                    username_input = await page.query_selector(selector)
                    if username_input:
                        _LOGGER.debug("Found username input with selector: %s", selector)
                        break
                except Exception:
                    continue

            if not username_input:
                # Try getting first text input
                username_input = await page.query_selector('input[type="text"]')

            if not username_input:
                raise AntelAuthError("Could not find username input field")

            # Fill username
            await username_input.fill(self._username)

            # Try different possible selectors for password field
            password_selectors = [
                'input[name="password"]',
                'input[name="pass"]',
                'input[type="password"]',
                'input[id*="password"]',
                'input[id*="pass"]',
                '#password',
                '#pass',
            ]

            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.query_selector(selector)
                    if password_input:
                        _LOGGER.debug("Found password input with selector: %s", selector)
                        break
                except Exception:
                    continue

            if not password_input:
                raise AntelAuthError("Could not find password input field")

            # Fill password
            await password_input.fill(self._password)

            # Try different possible selectors for submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Ingresar")',
                'button:has-text("Iniciar")',
                'button:has-text("Entrar")',
                'button:has-text("Login")',
                '.btn-login',
                '.login-button',
                '#login-button',
                '#submit',
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await page.query_selector(selector)
                    if submit_button:
                        _LOGGER.debug("Found submit button with selector: %s", selector)
                        break
                except Exception:
                    continue

            if submit_button:
                await submit_button.click()
            else:
                # Try pressing Enter on password field
                await password_input.press("Enter")

            # Wait for navigation after login
            await page.wait_for_load_state("networkidle", timeout=30000)

            # Check for login errors
            error_selectors = [
                '.error',
                '.alert-danger',
                '.login-error',
                '[class*="error"]',
                '[class*="invalid"]',
            ]

            for selector in error_selectors:
                error_element = await page.query_selector(selector)
                if error_element:
                    error_text = await error_element.text_content()
                    if error_text and len(error_text.strip()) > 0:
                        _LOGGER.error("Login error detected: %s", error_text)
                        raise AntelAuthError(f"Login failed: {error_text}")

            _LOGGER.debug("Login successful")
            return True

        except PlaywrightTimeout as err:
            _LOGGER.error("Timeout during login: %s", err)
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
            # Wait for consumption data to load
            await page.wait_for_load_state("networkidle", timeout=30000)

            # Give some time for dynamic content to load
            await asyncio.sleep(2)

            # Get page content for debugging
            page_content = await page.content()
            _LOGGER.debug("Page content length: %d", len(page_content))

            # Try to find consumption data - these selectors need to be adjusted
            # based on the actual page structure

            # Common patterns for data consumption display
            consumption_selectors = [
                # Progress bars
                '.progress-bar',
                '[class*="progress"]',
                '[class*="consumo"]',
                '[class*="usage"]',
                # Data display elements
                '.data-usage',
                '.consumption-data',
                '.internet-usage',
                '[class*="data"]',
                # Specific text patterns
                'text=/\\d+[.,]?\\d*\\s*(GB|MB|TB)/i',
            ]

            # Try to find used data
            used_data_patterns = [
                '[class*="usado"]',
                '[class*="used"]',
                '[class*="consumido"]',
                ':has-text("Usado")',
                ':has-text("Consumido")',
            ]

            for selector in used_data_patterns:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text:
                            raw_data['used_element'] = text
                            value = self._parse_data_value(text)
                            if value is not None:
                                data.used_data_gb = value
                                _LOGGER.debug("Found used data: %s GB", value)
                                break
                except Exception as e:
                    _LOGGER.debug("Error with selector %s: %s", selector, e)
                    continue

            # Try to find total data
            total_data_patterns = [
                '[class*="total"]',
                '[class*="plan"]',
                '[class*="disponible"]',
                ':has-text("Total")',
                ':has-text("Plan")',
            ]

            for selector in total_data_patterns:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text:
                            raw_data['total_element'] = text
                            value = self._parse_data_value(text)
                            if value is not None:
                                data.total_data_gb = value
                                _LOGGER.debug("Found total data: %s GB", value)
                                break
                except Exception as e:
                    _LOGGER.debug("Error with selector %s: %s", selector, e)
                    continue

            # Try to extract all text and find data patterns
            body_text = await page.inner_text('body')
            raw_data['body_text_sample'] = body_text[:1000] if body_text else None

            # Look for GB/MB patterns in text
            data_matches = re.findall(r'([\d.,]+)\s*(GB|MB|TB)', body_text, re.IGNORECASE)
            if data_matches:
                raw_data['data_matches'] = data_matches
                _LOGGER.debug("Found data patterns: %s", data_matches)

                # If we don't have used/total yet, try to infer from matches
                if data.used_data_gb is None and len(data_matches) >= 1:
                    value = float(data_matches[0][0].replace(',', '.'))
                    unit = data_matches[0][1].upper()
                    if unit == 'MB':
                        value /= 1024
                    data.used_data_gb = value

                if data.total_data_gb is None and len(data_matches) >= 2:
                    value = float(data_matches[1][0].replace(',', '.'))
                    unit = data_matches[1][1].upper()
                    if unit == 'MB':
                        value /= 1024
                    data.total_data_gb = value

            # Calculate remaining and percentage
            if data.used_data_gb is not None and data.total_data_gb is not None:
                data.remaining_data_gb = data.total_data_gb - data.used_data_gb
                if data.total_data_gb > 0:
                    data.percentage_used = (data.used_data_gb / data.total_data_gb) * 100

            # Try to find plan name
            plan_patterns = [
                '[class*="plan"]',
                '[class*="nombre"]',
                ':has-text("Plan")',
            ]

            for selector in plan_patterns:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text and 'GB' not in text.upper():
                            data.plan_name = text.strip()
                            raw_data['plan_name'] = text
                            break
                except Exception:
                    continue

            # Try to find billing period
            period_patterns = [
                '[class*="periodo"]',
                '[class*="fecha"]',
                '[class*="billing"]',
                ':has-text("Período")',
                ':has-text("Vence")',
            ]

            for selector in period_patterns:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text:
                            data.billing_period = text.strip()
                            raw_data['billing_period'] = text
                            break
                except Exception:
                    continue

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

            # Login
            await self._login(page)

            # Navigate to consumption page if not already there
            current_url = page.url
            if "consumo" not in current_url.lower():
                await page.goto(ANTEL_LOGIN_URL, wait_until="networkidle", timeout=60000)

            # Extract data
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
            await self._login(page)
            return True
        except AntelAuthError:
            return False
        finally:
            await context.close()

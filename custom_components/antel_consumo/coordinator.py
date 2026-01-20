"""Data coordinator for Antel Consumo integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .antel_scraper import (
    AntelScraper,
    AntelConsumoData,
    AntelScraperError,
    AntelAuthError,
    AntelConnectionError,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AntelConsumoCoordinator(DataUpdateCoordinator[AntelConsumoData]):
    """Coordinator for Antel consumption data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.scraper = AntelScraper(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> AntelConsumoData:
        """Fetch data from Antel."""
        try:
            _LOGGER.debug("Fetching Antel consumption data")
            data = await self.scraper.get_consumption_data()
            _LOGGER.debug(
                "Fetched data: used=%s GB, total=%s GB",
                data.used_data_gb,
                data.total_data_gb,
            )
            return data
        except AntelAuthError as err:
            _LOGGER.error("Authentication error: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except AntelConnectionError as err:
            _LOGGER.error("Connection error: %s", err)
            raise UpdateFailed(f"Connection failed: {err}") from err
        except AntelScraperError as err:
            _LOGGER.error("Scraper error: %s", err)
            raise UpdateFailed(f"Failed to fetch data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching Antel data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and close the scraper."""
        await self.scraper.close()

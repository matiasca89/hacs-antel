"""Config flow for Antel Consumo integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .antel_scraper import (
    AntelScraper,
    AntelAuthError,
    AntelConnectionError,
    AntelScraperError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class AntelConsumoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Antel Consumo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured with same username
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

            # Validate credentials
            scraper = AntelScraper(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )

            try:
                valid = await scraper.validate_credentials()
                if not valid:
                    errors["base"] = "invalid_auth"
            except AntelAuthError:
                errors["base"] = "invalid_auth"
            except AntelConnectionError:
                errors["base"] = "cannot_connect"
            except AntelScraperError:
                errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            finally:
                await scraper.close()

            if not errors:
                return self.async_create_entry(
                    title=f"Antel ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

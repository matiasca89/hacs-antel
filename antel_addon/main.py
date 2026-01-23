import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, date
import requests
from pathlib import Path

# Adjust path to find the package if needed
sys.path.append("/app")

from antel_pkg.antel_scraper import AntelScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AntelAddon")

# Supervisor API configuration
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
SUPERVISOR_API = "http://supervisor/core/api"
HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

# Daily tracking file
DAILY_DATA_FILE = Path("/data/daily_tracking.json")


def get_config():
    """Read config from /data/options.json"""
    config_path = Path("/data/options.json")
    if not config_path.exists():
        return {
            "username": os.environ.get("ANTEL_USER"),
            "password": os.environ.get("ANTEL_PASS"),
            "scan_interval": 60,
            "service_id": ""
        }
    with open(config_path, "r") as f:
        return json.load(f)


def load_daily_tracking():
    """Load daily tracking data from persistent storage."""
    if DAILY_DATA_FILE.exists():
        try:
            with open(DAILY_DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load daily tracking: {e}")
    return {}


def save_daily_tracking(data):
    """Save daily tracking data to persistent storage."""
    try:
        with open(DAILY_DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to save daily tracking: {e}")


def calculate_daily_consumption(current_used_gb: float) -> float:
    """Calculate today's consumption based on baseline."""
    today = date.today().isoformat()
    tracking = load_daily_tracking()
    
    # Check if we have a baseline for today
    if tracking.get("date") != today:
        # New day - set baseline to current value
        logger.info(f"New day detected ({today}). Setting baseline to {current_used_gb} GB")
        tracking = {
            "date": today,
            "baseline_gb": current_used_gb
        }
        save_daily_tracking(tracking)
        return 0.0
    
    # Calculate delta
    baseline = tracking.get("baseline_gb", current_used_gb)
    daily_consumption = max(0.0, current_used_gb - baseline)
    return round(daily_consumption, 2)


def update_sensor(entity_id, state, attributes=None, unit=None, icon=None, device_class=None):
    """Update a sensor state via Supervisor API."""
    url = f"{SUPERVISOR_API}/states/sensor.{entity_id}"
    payload = {
        "state": state,
        "attributes": attributes or {},
    }
    if unit:
        payload["attributes"]["unit_of_measurement"] = unit
    if icon:
        payload["attributes"]["icon"] = icon
    if device_class:
        payload["attributes"]["device_class"] = device_class
    
    # Friendly name attribute
    friendly_name = entity_id.replace("antel_", "Antel ").replace("_", " ").title()
    payload["attributes"]["friendly_name"] = friendly_name

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug(f"Updated {entity_id}: {state}")
    except Exception as e:
        logger.error(f"Failed to update sensor {entity_id}: {e}")


async def main():
    logger.info("Antel Consumo Add-on started")
    
    config = get_config()
    username = config.get("username")
    password = config.get("password")
    scan_interval = config.get("scan_interval", 60)  # Minutes
    service_id = config.get("service_id", "")
    
    if not username or not password:
        logger.error("Username and password are required in configuration")
        return

    while True:
        logger.info("Starting scrape cycle...")
        scraper = AntelScraper(username, password, service_id if service_id else None)
        try:
            data = await scraper.get_consumption_data()
            
            if data:
                logger.info(f"Raw Data: billing='{data.billing_period}', renewal={data.days_until_renewal}, used={data.used_data_gb}")
                
                # If extraction failed, log HTML sample to debug
                if data.used_data_gb is None and data.raw_data and data.raw_data.get("body_html_sample"):
                     logger.warning("Extraction failed! HTML Dump (first 2000 chars):")
                     logger.warning(data.raw_data["body_html_sample"][:2000])
                
                # Update main sensors
                if data.used_data_gb is not None:
                    update_sensor("antel_datos_usados", data.used_data_gb, unit="GB", icon="mdi:download")
                    
                    # Calculate and update daily consumption
                    daily_gb = calculate_daily_consumption(data.used_data_gb)
                    update_sensor(
                        "antel_consumo_hoy",
                        daily_gb,
                        unit="GB",
                        icon="mdi:calendar-today",
                        attributes={
                            "state_class": "total_increasing",
                            "last_reset": date.today().isoformat()
                        }
                    )
                    logger.info(f"Daily consumption: {daily_gb} GB")
                
                if data.total_data_gb is not None:
                    update_sensor("antel_datos_totales", data.total_data_gb, unit="GB", icon="mdi:database")
                
                if data.remaining_data_gb is not None:
                    update_sensor("antel_datos_restantes", data.remaining_data_gb, unit="GB", icon="mdi:database-check")
                
                if data.percentage_used is not None:
                    update_sensor("antel_porcentaje_usado", round(data.percentage_used, 1), unit="%", icon="mdi:percent")
                
                if data.plan_name:
                    update_sensor("antel_plan", data.plan_name, icon="mdi:file-document")
                
                if data.billing_period:
                    update_sensor("antel_periodo_facturacion", data.billing_period, icon="mdi:calendar")
                
                if data.days_until_renewal is not None:
                    update_sensor("antel_dias_para_renovar", data.days_until_renewal, unit="días", icon="mdi:calendar-refresh")
                
                if data.contract_end_date:
                    update_sensor("antel_fin_contrato", data.contract_end_date, icon="mdi:calendar-end")
                
                logger.info("Scrape finished successfully. Data updated.")
            else:
                logger.warning("Scrape finished but no data returned.")

        except Exception as e:
            logger.error(f"Error during scrape: {e}")
        finally:
            await scraper.close()
        
        logger.info(f"Sleeping for {scan_interval} minutes...")
        await asyncio.sleep(scan_interval * 60)


if __name__ == "__main__":
    asyncio.run(main())

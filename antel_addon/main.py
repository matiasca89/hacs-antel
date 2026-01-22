import asyncio
import json
import logging
import os
import sys
import time
import requests
from pathlib import Path

# Adjust path to find the package if needed, or assume installed
sys.path.append("/app")

# We will structure the container so this import works
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

def get_config():
    """Read config from /data/options.json"""
    config_path = Path("/data/options.json")
    if not config_path.exists():
        # Fallback for local testing
        return {
            "username": os.environ.get("ANTEL_USER"),
            "password": os.environ.get("ANTEL_PASS"),
            "scan_interval": 60
        }
    with open(config_path, "r") as f:
        return json.load(f)

def update_sensor(entity_id, state, attributes=None, unit=None, icon=None):
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
    
    # Friendly name attribute
    payload["attributes"]["friendly_name"] = entity_id.replace("antel_", "Antel ").replace("_", " ").title()

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
    scan_interval = config.get("scan_interval", 60) * 60  # Minutes to seconds? No, usually options are seconds or minutes. Let's assume minutes based on typical add-ons, or seconds. config.yaml says int. Let's interpret as minutes for "scan_interval" usually implies time between scans. But HA standard is usually seconds? 
    # Actually, default in const.py was 3600 (seconds). 
    # Let's assume input is in minutes for user friendliness in Add-on UI? 
    # Or seconds. Let's stick to minutes to be safe/user friendly or check standard. 
    # Let's interpret as MINUTES.
    
    if not username or not password:
        logger.error("Username and password are required in configuration")
        return

    # Initialize scraper
    # Note: AntelScraper uses playwright internally.
    # We need to manage the lifecycle carefully.
    
    while True:
        logger.info("Starting scrape cycle...")
        scraper = AntelScraper(username, password)
        try:
            data = await scraper.get_consumption_data()
            
            if data:
                # Update sensors
                if data.used_data_gb is not None:
                    update_sensor("antel_datos_usados", data.used_data_gb, unit="GB", icon="mdi:download")
                
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

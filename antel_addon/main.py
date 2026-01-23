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

# Spanish month names for parsing
SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}


def parse_billing_period(billing_period: str) -> tuple[date | None, date | None]:
    """Parse billing period like '1 de enero al 31 de enero' to dates."""
    if not billing_period:
        logger.warning("parse_billing_period received empty input")
        return None, None
    
    try:
        logger.info(f"Parsing billing period: '{billing_period}'")
        # Match pattern: "DD de MES al DD de MES"
        match = re.search(
            r'(\d{1,2})\s+de\s+(\w+)\s+al\s+(\d{1,2})\s+de\s+(\w+)',
            billing_period.lower()
        )
        if match:
            start_day = int(match.group(1))
            start_month = SPANISH_MONTHS.get(match.group(2))
            end_day = int(match.group(3))
            end_month = SPANISH_MONTHS.get(match.group(4))
            
            logger.info(f"Parsed dates: {start_day}/{start_month} to {end_day}/{end_month}")
            
            if start_month and end_month:
                year = date.today().year
                # Handle year wrap (e.g., December to January)
                start_date = date(year, start_month, start_day)
                if end_month < start_month:
                    end_date = date(year + 1, end_month, end_day)
                else:
                    end_date = date(year, end_month, end_day)
                return start_date, end_date
    except Exception as e:
        logger.warning(f"Failed to parse billing period '{billing_period}': {e}")
    
    return None, None


def calculate_days_elapsed(billing_period: str) -> int | None:
    """Calculate days elapsed since billing period start."""
    start_date, end_date = parse_billing_period(billing_period)
    if start_date:
        today = date.today()
        days_elapsed = (today - start_date).days + 1  # +1 to include start day
        logger.info(f"Start date: {start_date}, Today: {today}, Elapsed: {days_elapsed}")
        return max(1, days_elapsed)  # At least 1 day
    else:
        logger.warning(f"Could not calculate days elapsed. Start date not found for '{billing_period}'")
    return None


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
                
                # Calculate average usage sensors
                logger.info(f"Billing period raw: '{data.billing_period}'")
                logger.info(f"Days until renewal: {data.days_until_renewal}")
                
                days_elapsed = calculate_days_elapsed(data.billing_period)
                logger.info(f"Days elapsed calculated: {days_elapsed}")
                
                if days_elapsed and data.used_data_gb is not None:
                    avg_daily_usage = round(data.used_data_gb / days_elapsed, 2)
                    update_sensor(
                        "antel_promedio_uso_diario",
                        avg_daily_usage,
                        unit="GB/día",
                        icon="mdi:chart-line",
                        attributes={"days_elapsed": days_elapsed}
                    )
                    logger.info(f"Average daily usage: {avg_daily_usage} GB/day (over {days_elapsed} days)")
                
                if data.days_until_renewal and data.remaining_data_gb is not None:
                    if data.days_until_renewal > 0:
                        avg_remaining = round(data.remaining_data_gb / data.days_until_renewal, 2)
                        update_sensor(
                            "antel_promedio_restante_diario",
                            avg_remaining,
                            unit="GB/día",
                            icon="mdi:chart-timeline-variant",
                            attributes={"days_remaining": data.days_until_renewal}
                        )
                        logger.info(f"Average remaining per day: {avg_remaining} GB/day (over {data.days_until_renewal} days)")
                
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

"""Constants for the Antel Consumo integration."""

DOMAIN = "antel_consumo"

# URLs
ANTEL_LOGIN_URL = "https://aplicaciones.antel.com.uy/miAntel/consumo/internet"
ANTEL_BASE_URL = "https://aplicaciones.antel.com.uy"

# Update interval (1 hour)
DEFAULT_SCAN_INTERVAL = 3600

# Attributes
ATTR_USED_DATA = "used_data"
ATTR_TOTAL_DATA = "total_data"
ATTR_REMAINING_DATA = "remaining_data"
ATTR_PERCENTAGE_USED = "percentage_used"
ATTR_PLAN_NAME = "plan_name"
ATTR_BILLING_PERIOD = "billing_period"
ATTR_LAST_UPDATE = "last_update"

"""Constants for the Antel Consumo integration."""

DOMAIN = "antel_consumo"

# URLs
ANTEL_LOGIN_URL = (
    "https://www.antel.com.uy/acceder/-/login/openid_connect_request"
    "?p_p_state=maximized"
    "&_com_liferay_login_web_portlet_LoginPortlet_saveLastPath=false"
    "&_com_liferay_login_web_portlet_LoginPortlet_redirect=/"
    "&_com_liferay_login_web_portlet_LoginPortlet_OPEN_ID_CONNECT_PROVIDER_NAME=TuID"
)
ANTEL_CONSUMO_INTERNET_URL = "https://aplicaciones.antel.com.uy/miAntel/consumo/internet"
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

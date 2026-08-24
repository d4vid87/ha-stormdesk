"""Constants for the WeatherDesk integration."""

from datetime import timedelta

DOMAIN = "weatherdesk"

# The dashboard's own versioned endpoint. Everything else its server answers is shaped for its
# page and free to change with it; this one is a contract.
API_PATH = "/api/v1"

# The archive gains a row a minute at best, and this is a weather station rather than a doorbell.
# Sixty seconds is frequent enough that the card is never visibly stale and rare enough that a
# Raspberry Pi serving four dashboards does not notice.
SCAN_INTERVAL = timedelta(seconds=60)

# The sidebar entry pointing at the dashboard itself. Hide it the way any sidebar item is hidden
# — long-press the Home Assistant logo — rather than with a setting of our own.
PANEL_URL = "weatherdesk"

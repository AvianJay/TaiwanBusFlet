import config
from enum import Enum
import flet_geolocator as fg

if config.platform == "android":
    import android as current
elif config.platform == "ios":
    import ios as current
elif config.platform == "web":
    import web as current
else:
    current = None

class NetworkStatus(Enum):
    WIFI = "WIFI"
    CELLULAR = "CELLULAR"
    NO_NETWORK = "NO_NETWORK"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    OTHER = "OTHER"

def get_network_status():
    if current:
        status = current.get_network_status()
        return status
    else:
        return NetworkStatus.UNKNOWN

def create_shortcut(data, label):
    if current:
        return current.create_shortcut(data, label)
    else:
        return False

def update_app(url, page):
    if current:
        return current.update_app(url, page)
    else:
        page.launch_url(url)
        return True

GeolocatorSettings = current.GeolocatorSettings if current else fg.GeolocatorSettings(fg.GeolocatorPositionAccuracy.HIGH)

def wifilock(acquire=None):
    if current:
        return current.wifilock(acquire)
    else:
        return False

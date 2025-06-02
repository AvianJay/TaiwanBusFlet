import config
from enum import Enum

if config.platform == "android":
    import android as current
elif config.platform == "ios":
    import ios as current
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
        return current.create_shortcut()
    else:
        return False

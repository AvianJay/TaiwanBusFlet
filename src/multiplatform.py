import config

if config.platform == "android":
    import android as current
elif config.platform == "ios":
    import ios as current
else:
    current = None

WIFI = "WIFI"
CELLULAR = "CELLULAR"
NO_NETWORK = "NO_NETWORK"
FAILED = "FAILED"
UNKNOWN = "UNKNOWN"
OTHER = "OTHER"

def get_network_status():
    return current.get_network_status()
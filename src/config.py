import os
import json
import taiwanbus
from importlib.metadata import version

# info
app_version = "0.0.1"
config_version = 1
taiwanbus_version = version("taiwanbus")

# some global variables
current_bus = None
bus_update_time = 10  # seconds

platform = os.getenv("FLET_PLATFORM")
datadir = os.getenv("FLET_APP_STORAGE_DATA", ".")
taiwanbus.update_database_dir(datadir)
# taiwanbus bug, will be fixed in 0.1.0
taiwanbus.home = os.path.join(datadir, ".taiwanbus")

# config
default_config = {
    "config_version": config_version,
    "provider": "twn",
    "bus_update_time": 10,
}
config_path = os.path.join(datadir, "config.json")
config = None

if os.path.exists(config_path):
    config = json.load(open(config_path, "r"))
    # Todo: verify
else:
    config = default_config.copy()
    json.dump(config, open(config_path, "w"))

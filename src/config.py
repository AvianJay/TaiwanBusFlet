import os
import json
import taiwanbus
import flet as ft
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
_config = None

try:
    if os.path.exists(config_path):
        _config = json.load(open(config_path, "r"))
        # Todo: verify
    else:
        _config = default_config.copy()
        json.dump(_config, open(config_path, "w"))
except ValueError:
    _config = default_config.copy()
    json.dump(_config, open(config_path, "w"))

if _config.get("config_version", 0) < config_version:
    print("Updating config file from version", _config.get("config_version", 0), "to version", config_version)
    for k in default_config.keys():
        if not _config.get(k):
            _config[k] = default_config[k]

taiwanbus.update_provider(_config.get("provider"))

def config(key, value=None, mode="r"):
    if mode == "r":
        return _config.get(key)
    elif mode == "w":
        _config[key] = value
        json.dump(_config, open(config_path, "w"))
        return True
    else:
        raise ValueError("Invalid mode" + mode)

def get_time_text(stop: dict):
    if stop.get("msg"):
        return stop["msg"], ft.Colors.GREY_100, ft.Colors.PRIMARY
    elif stop["sec"] <= 0:
        return "進站中", ft.Colors.RED_900, ft.Colors.WHITE
    else:
        if stop["sec"] < 60:
            return str(stop["sec"]) + "秒", ft.Colors.RED_700, ft.Colors.WHITE
        else:
            minute = stop["sec"] // 60
            return str(minute) + "分", ft.Colors.RED_500 if minute < 3 else ft.Colors.GREY_200, ft.Colors.WHITE if minute < 3 else ft.Colors.PRIMARY

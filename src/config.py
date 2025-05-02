import os
import json
import taiwanbus
import flet as ft
# from importlib.metadata import version

# info
app_version = "0.0.1"
config_version = 2
# taiwanbus_version = version("taiwanbus")
# No package metadata when complied
# taiwanbus.__version__ will add in 0.1.0
taiwanbus_version = "0.0.9"

# some global variables
current_bus = None

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
    "bus_error_update_time": 10,
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
    _config["config_version"] = config_version
    print("Saving...")
    json.dump(_config, open(config_path, "w"))
    print("Done.")

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

def favorite_stop(favorite_name=None, mode="r", data=None):
    if mode == "r": # read
        try:
            with open(os.path.join(datadir, "favorite.json"), "r") as f:
                favorites = json.load(f)
                if favorite_name:
                    return favorites.get(favorite_name, [])
                else:
                    return favorites
        except FileNotFoundError:
            return [] if favorite_name else {}
    elif mode == "s": # set
        if not data:
            raise ValueError("data is None")
        if not favorite_name:
            raise ValueError("favorite_name is None")
        current_favorite = favorite_stop("r")
        current_favorite[favorite_name] = data
        with open(os.path.join(datadir, "favorite.json"), "w") as f:
            json.dump(current_favorite, f)
        return True
    elif mode == "d": # delete
        if not favorite_name:
            raise ValueError("favorite_name is None")
        current_favorite = favorite_stop("r")
        if data:
            current_favorite_with_name = current_favorite.get(favorite_name, [])
            if data not in current_favorite_with_name:
                return False
            current_favorite_with_name.remove(data)
            current_favorite[favorite_name] = current_favorite_with_name
        else:
            if favorite_name not in current_favorite:
                return False
            del current_favorite[favorite_name]
        with open(os.path.join(datadir, "favorite.json"), "w") as f:
            json.dump(current_favorite, f)
        return True
    else:
        raise ValueError("Invalid mode" + mode)

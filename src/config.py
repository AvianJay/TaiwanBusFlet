import os
import json
import taiwanbus
import flet as ft
# from importlib.metadata import version

# info
app_version = "0.0.1"
config_version = 4
# taiwanbus_version = version("taiwanbus")
# No package metadata when complied
# taiwanbus.__version__ will be added in 0.1.0
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
    "bus_error_update_time": 1,
    "always_show_second": False,
    "auto_update": "checkonly", # no, checkonly, all, wifi, cellular
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
        raise ValueError(f"Invalid mode: {mode}")

def get_time_text(stop: dict):
    if stop.get("msg"):
        stop["msg"] = "末班\n駛離" if stop["msg"] == "末班駛離" else stop["msg"]
        return stop["msg"], ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY), ft.Colors.PRIMARY
    elif stop["sec"] <= 0:
        return "進站中", ft.Colors.RED_900, ft.Colors.WHITE
    else:
        if stop["sec"] < 60:
            return str(stop["sec"]) + "秒", ft.Colors.RED_700, ft.Colors.WHITE
        else:
            minute = stop["sec"] // 60
            second_str = "\n" + str(stop["sec"] % 60) + "秒" if config("always_show_second") else ""
            return str(minute) + "分" + second_str, ft.Colors.RED_500 if minute < 3 else ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY), ft.Colors.WHITE if minute < 3 else ft.Colors.PRIMARY

def read_favorites():
    try:
        with open(os.path.join(datadir, "favorite.json"), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def favorite_stop(favorite_name=None, mode="r", data=None):
    if mode == "r": # read
        favorites = read_favorites()
        if favorite_name:
            return favorites.get(favorite_name, [])
        else:
            return favorites
    elif mode == "s": # set
        if data is None:
            raise ValueError("data is None")
        if not favorite_name:
            raise ValueError("favorite_name is None")
        with open(os.path.join(datadir, "favorite.json"), "r+", encoding="utf-8") as f:
            current_favorite = json.load(f)
            current_favorite[favorite_name] = data
            f.seek(0)
            json.dump(current_favorite, f)
            f.truncate()
        return True
    elif mode == "d": # delete
        if not favorite_name:
            raise ValueError("favorite_name is None")
        with open(os.path.join(datadir, "favorite.json"), "r+", encoding="utf-8") as f:
            current_favorite = json.load(f)
            if data:
                current_favorite_with_name = current_favorite.get(favorite_name, [])
                if data in current_favorite_with_name:
                    current_favorite_with_name.remove(data)
                else:
                    raise ValueError(f"Data '{data}' not found in the favorite list.")
                current_favorite[favorite_name] = current_favorite_with_name
            else:
                if favorite_name not in current_favorite:
                    return False
                del current_favorite[favorite_name]
            f.seek(0)
            json.dump(current_favorite, f)
            f.truncate()
        return True
    else:
        raise ValueError("Invalid mode" + mode)

if not os.path.exists(os.path.join(datadir, "favorite.json")):
    json.dump({}, open(os.path.join(datadir, "favorite.json"), "w"))

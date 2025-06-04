import os
import json
import math
import requests
import taiwanbus
import flet as ft
import flet_geolocator as fg
import threading
import multiplatform
# from importlib.metadata import version

# info
app_version = "0.0.1"
config_version = 6
# taiwanbus_version = version("taiwanbus")
# No package metadata when complied
# taiwanbus.__version__ will be added in 0.1.0
taiwanbus_version = "0.0.9"
update_channel = "release"

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
    "auto_update": "check_popup", # no, check_popup, check_notify, all, wifi, cellular
    "firstrun": True,
    "theme": "system",
}
config_path = os.path.join(datadir, "config.json")
_config = None

try:
    if os.path.exists(config_path):
        _config = json.load(open(config_path, "r"))
        # Todo: verify
        if not isinstance(_config, dict):
            print("Config file is not a valid JSON object, resetting to default config.")
            _config = default_config.copy()
        for key in _config.keys():
            if not isinstance(_config[key], type(default_config[key])):
                print(f"Config key '{key}' has an invalid type, resetting to default value.")
                _config[key] = default_config[key]
        if "config_version" not in _config:
            print("Config file does not have 'config_version', resetting to default config.")
            _config = default_config.copy()
    else:
        _config = default_config.copy()
        json.dump(_config, open(config_path, "w"))
except ValueError:
    _config = default_config.copy()
    json.dump(_config, open(config_path, "w"))

if _config.get("config_version", 0) < config_version:
    print("Updating config file from version", _config.get("config_version", 0), "to version", config_version)
    for k in default_config.keys():
        if _config.get(k) == None:
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
                ran = False
                for item in current_favorite_with_name:
                    if item.get("stopid") == data.get("stopid"):
                        current_favorite_with_name.remove(item)
                        ran = True
                        break
                if not ran:
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

position_change_events = []

def handle_position_change(e):
    print("Position changed:", e)
    for event in position_change_events:
        try:
            event(e)
        except Exception as ex:
            print("Error in position change event:", ex)

gl = fg.Geolocator(
        location_settings=multiplatform.GeolocatorSettings,
        on_position_change=handle_position_change,
        on_error=lambda e: print("Geolocator error:", e),
    )

def location_permission(request=True):
    try:
        if request:
            gl.request_permission(wait_timeout=60)
        print(gl.get_permission_status())
        return gl.get_permission_status()
    except:
        return False

def get_location(force=False):
    try:
        if location_permission() not in [fg.GeolocatorPermissionStatus.ALWAYS, fg.GeolocatorPermissionStatus.WHILE_IN_USE]:
            print("Location permission not granted.")
            return None
        try:
            if force:
                return gl.get_current_position()
            else:
                threading.Thread(target=gl.get_current_position, daemon=True).start()
                return gl.get_last_known_position()
        except Exception as e:
            print("Error getting location:", e)
            return None
    except Exception as e:
        print("Error getting location:", e)
        return None

# check updates
def check_update():
    global app_version
    if update_channel == "nightly":
        workflows_url = "https://api.github.com/repos/AvianJay/TaiwanBusFlet/actions/workflows"
        res = requests.get(workflows_url).json()
        workflow_url = next((s["url"] for s in res.get("workflows") if s["name"] == "Build"), None)
        if not workflow_url:
            return False, "Workflow not found"
        workflow_url += "/runs?per_page=1"
        res = requests.get(workflow_url).json()
        hash = res.get("workflow_runs")[0].get("head_sha")[0:7].strip().lower()
        app_version = app_version.strip().lower()
        if not hash == app_version:
            return f"New commit: {hash}\n\n**Full Changelog**: [{app_version}...{hash}](https://github.com/AvianJay/TaiwanBusFlet/compare/{app_version}...{hash})", f"https://nightly.link/AvianJay/TaiwanBusFlet/workflows/build/main/taiwanbusflet-{platform}.zip"
        return False, None
    return False, None

# thanks stackoverflow
def measure(lat1, lon1, lat2, lon2):
    R = 6378.137  # Radius of earth in KM
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dLon / 2) ** 2
         )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return d * 1000  # meters

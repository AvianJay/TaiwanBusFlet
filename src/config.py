import os
import taiwanbus

# some global variables
current_bus = None
bus_update_time = 10  # seconds

platform = os.getenv("FLET_PLATFORM")
datadir = os.getenv("FLET_APP_STORAGE_DATA")
taiwanbus.update_database_dir(datadir)
taiwanbus.home = os.path.join(datadir, ".taiwanbus")
print(datadir)

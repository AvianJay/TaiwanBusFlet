import os
import taiwanbus

# some global variables
current_bus = None

platform = os.getenv("FLET_PLATFORM")
datadir = os.getenv("FLET_APP_STORAGE_DATA")
taiwanbus.update_database_dir(datadir)

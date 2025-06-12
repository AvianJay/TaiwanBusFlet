import flet_geolocator as fg

def get_network_status():
    from multiplatform import NetworkStatus
    return NetworkStatus.UNKNOWN

def create_shortcut(data, label):
    return False

def update_app(url, page):
    page.launch_url(url)
    return True

GeolocatorSettings = fg.GeolocatorWebSettings(
    fg.GeolocatorPositionAccuracy.HIGH,
)

def wifilock(acquire):
    return False

from jnius import autoclass, cast
from multiplatform import NetworkStatus

def get_network_status():
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    activity = PythonActivity.mActivity

    connectivity_service = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
    ConnectivityManager = autoclass('android.net.ConnectivityManager')
    NetworkCapabilities = autoclass('android.net.NetworkCapabilities')
    Build = autoclass('android.os.Build')

    if Build.VERSION.SDK_INT >= 23:
        network = connectivity_service.getActiveNetwork()
        if network is None:
            return NetworkStatus.NO_NETWORK
        capabilities = connectivity_service.getNetworkCapabilities(network)

        if capabilities is None:
            return NetworkStatus.FAILED
        elif capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI):
            return NetworkStatus.WIFI
        elif capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR):
            return NetworkStatus.CELLULAR
        else:
            return NetworkStatus.OTHER
    else:
        return NetworkStatus.UNKNOWN

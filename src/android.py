from jnius import autoclass, cast
# from multiplatform import NetworkStatus
# fix circular import issue
import os

def get_network_status():
    from multiplatform import NetworkStatus
    # return NetworkStatus.UNKNOWN
    activity_host_class = os.getenv("MAIN_ACTIVITY_HOST_CLASS_NAME")
    assert activity_host_class is not None
    PythonActivity = autoclass(activity_host_class)
    if PythonActivity is None:
        return NetworkStatus.FAILED
    Context = autoclass('android.content.Context')
    activity = PythonActivity.mActivity

    connectivity_service = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
    ConnectivityManager = autoclass('android.net.ConnectivityManager')
    NetworkCapabilities = autoclass('android.net.NetworkCapabilities')
    Build = autoclass('android.os.Build')
    Version = autoclass('android.os.Build$VERSION')

    if Version.SDK_INT >= 23:
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

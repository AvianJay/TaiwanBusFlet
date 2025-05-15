from jnius import autoclass, cast
import multiplatform

def get_network_type():
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
            return multiplatform.UNKNOWN
        capabilities = connectivity_service.getNetworkCapabilities(network)

        if capabilities is None:
            return multiplatform.FAILED
        elif capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI):
            return multiplatform.WIFI
        elif capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR):
            return multiplatform.CELLULAR
        else:
            return multiplatform.OTHER
    else:
        return multiplatform.UNKNOWN

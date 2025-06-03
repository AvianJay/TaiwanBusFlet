from jnius import autoclass, cast
import os

Intent = autoclass("android.content.Intent")
PendingIntent = autoclass("android.app.PendingIntent")
ShortcutInfoBuilder = autoclass("android.content.pm.ShortcutInfo$Builder")
ShortcutManager = autoclass("android.content.pm.ShortcutManager")
ComponentName = autoclass("android.content.ComponentName")
Uri = autoclass("android.net.Uri")
Class = autoclass("java.lang.Class")

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
    print("SDK Version:", str(Version.SDK_INT))

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

def create_shortcut(data, label):
    # 1. 拿到 context 和 ShortcutManager
    activity_host_class = os.getenv("MAIN_ACTIVITY_HOST_CLASS_NAME")
    assert activity_host_class is not None
    PythonActivity = autoclass(activity_host_class)
    context = PythonActivity.mActivity
    shortcut_manager = cast("android.content.pm.ShortcutManager", context.getSystemService(Class.forName("android.content.pm.ShortcutManager")))

    # 2. 檢查是否支援釘選捷徑
    if shortcut_manager.isRequestPinShortcutSupported():
        # 3. 建立啟動 Intent
        shortcut_intent = Intent(Intent.ACTION_MAIN)
        shortcut_intent.setClassName("tw.avianjay.taiwanbusflet", "tw.avianjay.taiwanbusflet.MainActivity")
        shortcut_intent.setData(Uri.parse(data))
        shortcut_intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK)

        # 4. 建立 ShortcutInfo
        ShortcutInfoBuilder = autoclass("android.content.pm.ShortcutInfo$Builder")
        shortcut_info = ShortcutInfoBuilder(context, "busview-shortcut") \
            .setShortLabel(label) \
            .setLongLabel(label) \
            .setIntent(shortcut_intent) \
            .build()

        # 5. 建立回呼用的 PendingIntent（可略）
        pinned_intent = shortcut_manager.createShortcutResultIntent(shortcut_info)
        flag_immutable = PendingIntent.FLAG_IMMUTABLE
        pending_intent = PendingIntent.getBroadcast(
            context, 0, pinned_intent, flag_immutable
        )

        # 6. 請求建立捷徑
        shortcut_manager.requestPinShortcut(
            shortcut_info,
            pending_intent.getIntentSender()
        )
        return True
    else:
        return False

# from multiplatform import NetworkStatus
# fix circular import issue

def get_network_status():
    from multiplatform import NetworkStatus
    return NetworkStatus.UNKNOWN
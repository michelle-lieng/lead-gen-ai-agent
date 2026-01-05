from api.base import ApiError, NetworkError
from .ui_errors import show_api_error, show_network_error

def call_api(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except NetworkError as e:
        show_network_error(e)
        return None
    except ApiError as e:
        show_api_error(e)
        return None
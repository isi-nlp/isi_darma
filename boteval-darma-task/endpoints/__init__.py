from ._interface import Endpoint
from ._loader import EndpointsLoader

def init_endpoints():
    _loader = EndpointsLoader()
    return {
        k: cls().query
        for k, cls in _loader._endpoints.items()
    }

endpoints_dict = init_endpoints()
        
"""
This script is serving as an automatic loader for Endpoints; its implementation was adapted from `Scrapy` library and its `spiderloader.py` approach

Sources:
- https://github.com/scrapy/scrapy/blob/master/scrapy/spiderloader.py

"""

import inspect
import warnings
import traceback
import logging as log
from importlib import import_module
from pkgutil import iter_modules
from collections import defaultdict

from . import Endpoint

def walk_modules(path):
    """Loads a module and all its submodules from the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.
    For example: walk_modules('scrapy.utils')
    """
    
    mods = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, "__path__"):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + "." + subpath
            if ispkg:
                mods += walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)
    return mods

def iter_endpoint_classes(module):
    """Return an iterator over all endpoint classes defined in the given module
    that can be instantiated (i.e. which have name)
    """

    for obj in vars(module).values():
        if (
            inspect.isclass(obj)
            and issubclass(obj, Endpoint)
            and obj.__module__ == module.__name__
            and getattr(obj, "name", None)
        ):
            yield obj
            
class EndpointsLoader:
    def __init__(self, warn_only=False, endpoints_modules=['endpoints']):
        self.endpoints_modules = endpoints_modules
        self.warn_only = warn_only
        self._endpoints = {}
        self._found = defaultdict(list)
        self._load_all_endpoints()
        
    def _check_name_duplicates(self):
        dupes = []
        for name, locations in self._found.items():
            dupes.extend(
                [
                    f"  {cls} named {name!r} (in {mod})"
                    for mod, cls in locations
                    if len(locations) > 1
                ]
            )

        if dupes:
            dupes_string = "\n\n".join(dupes)
            warnings.warn(
                "There are several endpoints with the same name:\n\n"
                f"{dupes_string}\n\n  This can cause unexpected behavior.",
                category=UserWarning,
            )

    def _load_all_endpoints(self):
            for name in self.endpoints_modules:
                try:
                    for module in walk_modules(name):
                        self._load_endpoints(module)
                except ImportError:
                    if self.warn_only:
                        log.warn(
                            f"\n{traceback.format_exc()}Could not load endpoint "
                            f"from module '{name}'. "
                            "See above traceback for details.",
                            category=RuntimeWarning,
                        )
                    else:
                        raise
            self._check_name_duplicates()
            
            
    def _load_endpoints(self, module):
            for spcls in iter_endpoint_classes(module):
                self._found[spcls.name].append((module.__name__, spcls.__name__))
                self._endpoints[spcls.name] = spcls
    
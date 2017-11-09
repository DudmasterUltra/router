"""The python interface for your router

rout3r can automatically scan common default router gateway IPs and determine the router model,
or be provided with a solid IP address to connect to. Note: if the router is unreachable, fallbacks
may pose a security risk that can be avoided by disabling them"""
__author__ = "ex0dus"
__version__ = "1.0"

from requests.exceptions import ConnectionError
import abc, pkgutil, os, importlib, requests

NON_ROUTER_MODULES = ["__init__"]
ROUTER_MODULES = [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(__file__)])
                  if name not in NON_ROUTER_MODULES]
__all__ = ROUTER_MODULES

DEFAULT_IP = "192.168.1.1"
ENABLE_FALLBACK_DEFAULT_IPS = True
FALLBACK_DEFAULT_IPS = [

    "192.168.0.1", "192.168.1.254", "192.168.2.1",
    "10.0.0.1", "10.0.0.2", "10.1.1.1"

]
"""Note: using the fallback IPs may pose a security risk if the router is unreachable"""

def get_public_ip():
    """Retrieve your public IP address (using ipify)"""
    return requests.get('https://api.ipify.org').text

class RouterResult:
    """A result object returned by automatic methods which find routers containing the
    router class and IP address"""
    Class = None
    ip_address = None

    def __init__(self, Class, ip_address):
        self.Class = Class
        self.ip_address = ip_address

    def __call__(self, *args, **kwargs):
        return self.Class.__call__(*args, **kwargs)

class RouterClient:
    """An object to describe characteristics about clients connected to the router"""
    name = None
    ip_address = None
    mac_address = None
    connection_type = None

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

class Router(object, metaclass=abc.ABCMeta):
    """An abstract router class which all module router classes should extend"""
    manufacturer = None
    model = None
    firmware = None
    
    def __init__(self, username, password, ip_address=DEFAULT_IP):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should check the status of the WAN connection in the router"""
    @abc.abstractmethod
    def is_online(self):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should return the router firmware version as an int or string"""
    @abc.abstractmethod
    def get_firmware(self):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should reboot the router"""
    @abc.abstractmethod
    def reboot(self):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should get the network SSID"""
    @abc.abstractmethod
    def get_ssid(self):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should set the network SSID"""
    @abc.abstractmethod
    def set_ssid(self, ssid):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should get the network key / password (if supported)"""
    @abc.abstractmethod
    def get_key(self):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should end the current session with the router gateway and not raise any exceptions"""
    @abc.abstractmethod
    def logout(self):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

    """This method should return True when the gateway HTML matches this router model ONLY, otherwise return False"""
    @staticmethod
    @abc.abstractmethod
    def check_model(gateway):
        raise NotImplementedError("{0} is missing this implementation".format(self.__class__.__name__))

__routers__ = [Router]
"""All rout3r modules require a list of their router classes"""

def get_router(ip_address=DEFAULT_IP, test_fallbacks=ENABLE_FALLBACK_DEFAULT_IPS):
    """Attempt to automatically get the router IP address and model, and optionally check fallback IPs"""
    test_ips = [ip_address] + (FALLBACK_DEFAULT_IPS if test_fallbacks else [])
    for ip in test_ips:
        try:
            result = requests.get("http://{0}/".format(ip))
            for router_module in ROUTER_MODULES:
                _import = importlib.import_module("{pack}.{module}".format(
                    pack=__package__,
                    module=router_module))
                if not hasattr(_import, "__routers__"):
                    raise NotImplementedError("Module {0} is missing __routers__ list".format(_import))
                for router_class in _import.__routers__:
                    if router_class.check_model(result.text) is True:
                        return RouterResult(router_class, ip)
            raise NotImplementedError("The router at {ip} does not have a module, or cannot be determined automatically".format(
                ip=ip))
        except ConnectionError:
            pass
    raise Exception("Unable to reach or determine router gateway IP address")


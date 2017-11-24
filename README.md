# router
The Python interface for your router

This framework "standardizes" router control for your program. Currently, the
only module is for Actiontec routers. However, I am open to pull requests and
I will be adding more including Asus router interfaces in the future.

The interface can also use heuristics to automatically identify the router model
by the gateway, which can be automatically searched for a default IP addresses or
a supplied address. Note: Fallback IPs may pose a security risk if the "real" router
is unreachable. Disabling fallbacks can fix this problem.

I have also included an example program that will run in the background and reboot your
router whenever the WAN is unreachable.

Dependencies: requests

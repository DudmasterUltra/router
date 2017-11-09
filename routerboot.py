"""The automatic router rebooter for Python"""
__author__ = "ex0dus"
__version__ = "1.0"

import logging, time, rout3r

logging.basicConfig(level = logging.INFO, format='[%(asctime)s: %(levelname)s] %(message)s')
log = logging.getLogger()
log.info("Routerboot {ver} starting up...".format(ver=__version__))
Model = rout3r.get_router("192.168.0.1", False) # Use your router's gateway IP here
log.info("Model: {0}".format(Model))

def login():
    return Router("username", "password") # Use your router gateway password here

def run():
    router = login()
    online = router.is_online()
    previous_online = online
    log.info("Routerboot connected - {ssid} is {status}".format(
        ssid=router.get_ssid(),
        status="online" if online else "offline"))
    try:
        while True:
            try:
                if router is None or not router.logged_in:
                    try:
                        router = login()
                        log.info("Routerboot reconnected, idling for 30 seconds while internet reconnects")
                        time.sleep(30)
                        log.info("Continuing to test connectivity")
                    except Exception:
                        pass
                online = False if router is None else router.is_online()
                if previous_online != online:
                    log.info("Network status changed - You are now {status}".format(
                        status="online" if online else "offline"))
                if not online and router is not None:
                    log.info("Requesting reboot, idling for 20 seconds")
                    router.reboot()
                    time.sleep(20)
                previous_online = online
            except Exception as e:
                if router is not None:
                    log.info("Routerboot disconnected and polling")
                    router = None
            time.sleep(3)
            
    except KeyboardInterrupt:
        pass
    log.info("Routerboot shutting down")
    router.logout()

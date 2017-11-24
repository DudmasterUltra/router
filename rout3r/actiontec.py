"""Actiontec router interfaces for rout3r"""
__author__ = "ex0dus"
__version__ = "1.1"

import requests, base64, rout3r

def _scrape(text, start, end):
    start_index = text.index(start) + len(start) + 1
    return text[start_index:text.index(end, start_index)]

class C1000A(rout3r.Router):

    manufacturer = "CenturyLink"
    model = "C1000A"
    firmware = "CAC003-31.30L.86"
    
    def __init__(self, username, password, ip_address=rout3r.DEFAULT_IP):
        self.ip_address = ip_address
        self.logged_in = False
        get = requests.get("http://{0}/".format(ip_address))
        if "sessionKey" in get.text:
            session_key = _scrape(get.text, "var sessionKey = '", "'")
            requests.post("http://{0}/login.cgi".format(ip_address), params={

                "adminUserName": username,
                "adminPassword": base64.b64encode(password.encode("utf-8")),
                "sessionKey": session_key,
                "nothankyou": 1

            })
            result = requests.get("http://{0}/login.html".format(ip_address))
            if "not valid" in result.text:
                raise Exception("Invalid credentials")
        self.logged_in = True

    def __del__(self):
        self.logout()

    def get_clients(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        get = requests.get("http://{0}/modemstatus_activeuserlist_refresh.html".format(self.ip_address))
        host_info = get.text.split("|")
        clients = []
        for host in host_info:
            if " " not in host:
                continue
            client = rout3r.RouterClient()
            space = host.index(" ")
            client.ip_address = host[:space]
            client.name = _scrape(host, "&#40", "&#41;")
            host = host[host.index("/", host.index("/") + 1) + 1:]
            slash = host.index("/")
            client.mac_address = host[:slash]
            host = host[slash + 1:]
            connection_type = host[:host.index("/")]
            if connection_type == "802.11":
                client.connection_type = "wifi"
            elif connection_type == "Ethernet":
                client.connection_type = connection_type.lower()
            else:
                client.connection_type = "unknown"
            clients.append(client)
        return clients

    def get_firmware(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        get = requests.get("http://{0}/modemstatus_home.html".format(self.ip_address))
        return _scrape(get.text, "var soft_ver=", "'")

    def is_online(self):
        if not self.logged_in:
            return False
        get = requests.get("http://{0}/modemstatus_home.html".format(self.ip_address))
        phy_status = _scrape(get.text, "var phy_status=", "'").lower()
        ISP_status = _scrape(get.text, "var ISP_status=", "'").lower()
        return not (("not" in phy_status) or ("not" in ISP_status))

    def reboot(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        result = requests.post("http://{0}/rebootinfo.cgi".format(self.ip_address), params={

            "Reboot": 1

        })
        if result.status_code == 200:
            self.logged_in = False
            return True
        return False

    def get_ssid(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        get = requests.get("http://{0}/wirelesssetup_basicsettings.html".format(self.ip_address))
        return _scrape(get.text, "gv_ssid = ", "\"")

    def set_ssid(self, ssid):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        post = requests.post("http://{0}/wirelesssetup_basicsettings.wl".format(self.ip_address), params={

            "wlRadio": 1,
            "wlSsid_wl0v0": ssid,
            "aeiwlDisabledByGui": 0,
            "needthankyou": 1

        })

    def enable_radio(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        post = requests.post("http://{0}/wirelesssetup_basicsettings.wl".format(self.ip_address), params={

            "wlRadio": 1,
            "wlSsid_wl0v0": self.get_ssid(),
            "aeiwlDisabledByGui": 0,
            "needthankyou": 1

        })

    def disable_radio(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        post = requests.post("http://{0}/wirelesssetup_basicsettings.wl".format(self.ip_address), params={

            "wlRadio": 0,
            "wlSsid_wl0v0": self.get_ssid(),
            "aeiwlDisabledByGui": 0,
            "needthankyou": 1

        })

    def get_key(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        get = requests.get("http://{0}/wirelesssetup_basicsettings.html".format(self.ip_address))
        return _scrape(get.text, "gv_wpapsk_key  =", "\"")

    def logout(self):
        if self.logged_in:
            self.logged_in = False
            try:
                requests.post("http://{0}/logout.cgi".format(self.ip_address))
            except:
                pass

    @staticmethod
    def check_model(gateway, ip):
        return ("Actiontec C1000A" in gateway) or ("var board_id='C1000A';" in gateway)

__routers__ = [C1000A]

"""Asus router interfaces for rout3r"""
__author__ = "ex0dus"
__version__ = "1.0"

import requests, base64, rout3r, json, datetime, random, urllib.parse
import xml.etree.ElementTree as ET
import time as _time

def millis():
    return int(round(_time.time() * 1000))

def _scrape(text, start, end):
    start_index = text.index(start) + len(start) + 1
    return text[start_index:text.index(end, start_index)]

def _encode_authorization(username, password):
    return base64.urlsafe_b64encode((username + ":" + password).encode("utf-8")).decode("utf-8")

def _make_headers(page):
    return { "Host": "router.asus.com", "Referer": "http://router.asus.com/" + str(page) }

class AsusRouterClient(rout3r.RouterClient):
    """Asus-specific router client characteristics"""
    vendor = None
    internet_allowed = True
    ip_method = None
    nickname = None

class RTAC68U(rout3r.Router):
    
    manufacturer = "Asus"
    model = "RT-AC68U"
    firmware = "3.0.0.4"
    connection_types = ("wired", "wifi 2.4GHz", "wifi 5GHz/5GHz-1", "wifi 5Ghz-2")
    _failure_str = "<script>top.location.href='/Main_Login.asp';"
    
    def __init__(self, username, password, ip_address=rout3r.DEFAULT_IP):
        self.ip_address = ip_address
        self._session = requests.Session()
        self._session.get("http://{}/Main_Login.asp".format(ip_address))
        response = self._session.post("http://{}/login.cgi".format(ip_address), data={

                "group_id": "",
                "action_mode": "",
                "action_script": "",
                "action_wait": 5,
                "current_page": "Main_Login.asp",
                "next_page": "index.asp",
                "login_authorization": _encode_authorization(username, password)

        }, headers=_make_headers("Main_Login.asp"))
        if "asus_token" in self._session.cookies:
            self.logged_in = True
        else:
            raise Exception("Invalid credentials")

    def __del__(self):
        self.logout()

    def _get_ajax_status(self):
        result = self._session.get("http://{}/ajax_status.xml".format(self.ip_address), params={

            "hash": random.uniform(0, 1)
        
        }, headers=_make_headers("index.asp"))
        result.encoding = "utf-8-sig"
        return result.text

    def _get_advanced_wireless_content(self):
        return self._session.get("http://{}/Advanced_Wireless_Content.asp".format(self.ip_address),
                                 headers=_make_headers("Advanced_Wireless_Content.asp")).text

    def get_uptime(self):
        result = self._get_ajax_status()
        if self._failure_str in result:
            self._force_logout()
        tree = ET.fromstring(result)
        for x in tree:
            if x.text and "secs since boot" in x.text:
                return datetime.timedelta(seconds=
                                         int(x.text[x.text.index("(") + 1:x.text.index("secs")]))
        return None

    def get_clients(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        response = self._session.get("http://{}/update_clients.asp".format(self.ip_address), params={

            "_": millis()
            
        }, headers=_make_headers("index.asp"))
        if self._failure_str in response.text:
            self._force_logout()
        response_json = json.loads(_scrape(response.text, "fromNetworkmapd :", "nmpClient").strip()[:-1])
        result = list()
        for key, element in response_json[0].items():
            if key == "maclist":
                continue
            client = AsusRouterClient()
            client.name = element["name"]
            client.ip_address = element["ip"]
            client.mac_address = key
            client.is_online = element["isOnline"] == 1
            vendor = element["vendor"]
            client.vendor = None if not vendor else vendor
            nickname = element["nickName"]
            client.nickname = None if not nickname else nickname
            client.ip_method = element["ipMethod"]
            client.internet_allowed = element["internetMode"] == "allow"
            client.radio_strength = int(element["rssi"])
            connection_type = element["isWL"]
            if connection_type:
                try:
                    client.connection_type = self.connection_types[int(connection_type)]
                except:
                    client.connection_type = "unknown"
            else:
                client.connection_type = "unknown"
            result.append(client)
        return result

    def get_firmware(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        response = self._session.get("http://{}/index.asp".format(self.ip_address),
                                     headers=_make_headers("index.asp"))
        if self._failure_str in response.text:
            self._force_logout()
        return _scrape(response.text, "\"firmver\" value=", "\">")

    def is_online(self):
        if not self.logged_in:
            return False
        response = self._session.get("http://{}/index.asp".format(self.ip_address),
                                     headers=_make_headers("index.asp"))
        if self._failure_str in response.text:
            self._force_logout()
        return _scrape(response.text, "wanlink_statusstr() { return ", "'") == "Connected"

    def reboot(self): # Untested
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        result = self._session.post("http://{}/apply.cgi".format(self.ip_address), data={

                "action_mode": "reboot",
                "action_script": "",
                "action_wait": 140

        }, headers=_make_headers("apply.asp"))
        if result.status_code == 200:
            self.logged_in = False
            return True
        return False

    def get_key(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        result = self._get_advanced_wireless_content()
        if self._failure_str in result:
            self._force_logout()
        return urllib.parse.unquote(_scrape(result, "\"wl_wpa_psk_org\" value=", "\">"))

    def set_ssid(self, ssid):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")

    def enable_radio(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")

    def disable_radio(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")

    def get_ssid(self):
        if not self.logged_in:
            raise rout3r.RouterLoggedOutException("This object has been logged out")
        result = self._get_advanced_wireless_content()
        if self._failure_str in result:
            self._force_logout()
        return urllib.parse.unquote(_scrape(result, "\"wl_ssid_org\" value=", "\">"))

    def _force_logout(self):
        self.logout()
        raise rout3r.RouterLoggedOutException("This object is now logged out")

    def logout(self):
        if self.logged_in:
            self.logged_in = False
            try:
                self._session.get("http://{}/Logout.asp".format(self.ip_address),
                                  headers=_make_headers("Logout.asp"))
            except:
                pass

    @staticmethod
    def check_model(gateway, ip):
        return "top.location.href='/Main_Login.asp';" in gateway \
               and "RT-AC68U" in requests.get("http://{}/Main_Login.asp".format(ip)).text

__routers__ = [RTAC68U]

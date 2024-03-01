import time
import requests
import traceback

COOKIES = ["_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|"]
WEBHOOK = ""
GROUP_ID = 0
class Bypass:
    def __init__(self, robloxCookie):
        self.cookie = robloxCookie
    
    def start_process(self):
        self.xcsrf_token = self.get_csrf_token()
        self.rbx_authentication_ticket = self.get_rbx_authentication_ticket()
        return self.get_set_cookie()
        
    def get_set_cookie(self):
        response = requests.post("https://auth.roblox.com/v1/authentication-ticket/redeem", headers={"rbxauthenticationnegotiation":"1"}, json={"authenticationTicket": self.rbx_authentication_ticket})
        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header, "An error occurred while getting the set_cookie"
        return set_cookie_header.split(".ROBLOSECURITY=")[1].split(";")[0]

        
    def get_rbx_authentication_ticket(self):
        response = requests.post("https://auth.roblox.com/v1/authentication-ticket", headers={"rbxauthenticationnegotiation":"1", "referer": "https://www.roblox.com/camel", 'Content-Type': 'application/json', "x-csrf-token": self.xcsrf_token}, cookies={".ROBLOSECURITY": self.cookie})
        assert response.headers.get("rbx-authentication-ticket"), "An error occurred while getting the rbx-authentication-ticket"
        return response.headers.get("rbx-authentication-ticket")
        
        
    def get_csrf_token(self) -> str:
        response = requests.post("https://auth.roblox.com/v2/logout", cookies = {".ROBLOSECURITY": self.cookie})
        xcsrf_token = response.headers.get("x-csrf-token")
        assert xcsrf_token, "An error occurred while getting the X-CSRF-TOKEN. Could be due to an invalid Roblox Cookie"
                 
        return xcsrf_token
    
class RobloxCookie:
    def __init__(self, cookie):
        self.cookie = cookie
        self._x_token = None
        self.last_generated_time = 0
        self.generate_token()

    def generate_token(self):
        self._x_token = requests.post("https://economy.roblox.com/", cookies={".ROBLOSECURITY": self.cookie}).headers.get("x-csrf-token")
        self.last_generated_time = time.time()

    def x_token(self):
        current_time = time.time()
        if current_time - self.last_generated_time >= 120:
            self.generate_token()
        return self._x_token

class RobloxAllySender:
    def __init__(self, roblox_cookie):
        self.cookie = roblox_cookie
        self.current_cursor = ''
        self.already_added = []

    def scrape_assets(self):
        items =  requests.get(f"https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&salesTypeFilter=1&sortType=3&subcategory=ClassicShirts&cursor={self.current_cursor}", 
                            cookies={".ROBLOSECURITY": self.cookie.get_current().cookie}, 
                            headers={"x-csrf-token": self.cookie.get_current().x_token()})
        if items.status_code != 200:
            return []
        return [item['id'] for item in items.json()["data"]]

    def sort_assets(self, ids):
        response = requests.post("https://catalog.roblox.com/v1/catalog/items/details", 
                                json={"items": [{"itemType": "Asset", "id": id} for id in ids]},
                                cookies={".ROBLOSECURITY": self.cookie.get_current().cookie},
                                headers={"x-csrf-token": self.cookie.get_current().x_token()})
        if response.status_code != 200:
            return []
        groups = []
        for item in response.json()["data"]:
            if item["creatorType"] == "Group" and item["creatorTargetId"] not in self.already_added:
                self.already_added.append(item["creatorTargetId"])
                groups.append(item["creatorTargetId"])
        return groups

    def get_allies_group(self, group_id):
        response = requests.get(f"https://groups.roproxy.com/v1/groups/{group_id}/relationships/allies?maxRows=100&sortOrder=Asc&startRowIndex=0", cookies={".ROBLOSECURITY": self.cookie.get_current().cookie}, headers={"x-csrf-token": self.cookie.get_current().x_token()})
        if response.status_code != 200:
           return []
        groups = []
        for group in response.json()["relatedGroups"]:
           if group["id"] not in self.already_added:
              self.already_added.append(group["id"])
              groups.append(group["id"])
        return groups

    def send_ally_request(self, group_id):
        response = requests.post(f"https://groups.roproxy.com/v1/groups/14116868/relationships/allies/{group_id}",
                                cookies={".ROBLOSECURITY": self.cookie.get_current().cookie}, 
                                headers={"x-csrf-token": self.cookie.get_current().x_token()})
        if response.status_code == 200:
            requests.post(WEBHOOK, json={"content": f"Sent ally request to group: {group_id}"})
        else:
            requests.post(WEBHOOK, json={"content": response.text})

    def start_process(self):
        while True:
          try:
            for group in self.sort_assets(self.scrape_assets()):
              allies = [group]
              while True:
               if not allies: break
               for group in allies:
                allies.remove(group)
                self.send_ally_request(group)
                next(self.cookie)
                time.sleep(60 / len(COOKIES))
                allies += self.get_allies_group(group)
          except Exception as e:
              requests.post(WEBHOOK, json={"content": f"ERROR: {traceback.format_exc()}"})
    
class iterator:
    def __init__(self, iterable):
        self.iterable = iterable
        self.length = len(iterable)
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < self.length:
            self.index += 1
        else:
            self.index = 0

    def get_current(self):
        if self.index < self.length:
            return self.iterable[self.index]
        else:
            self.index = 0
            return self.iterable[0]

ally_sender = RobloxAllySender(iterator([RobloxCookie(Bypass(cookie).start_process()) for cookie in COOKIES]))
ally_sender.start_process()

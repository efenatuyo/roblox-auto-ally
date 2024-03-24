import time, random

class Bypass:
    async def run(self, robloxCookie, session, proxy):
        self.cookie = robloxCookie
        self.xcsrf_token = await self.get_csrf_token(session, proxy)
        self.rbx_authentication_ticket = await self.get_rbx_authentication_ticket(session, proxy)
        return await self.get_set_cookie(session, proxy)
    
    async def get_set_cookie(self, session, proxy):
        response = await session.post("https://auth.roblox.com/v1/authentication-ticket/redeem", headers={"rbxauthenticationnegotiation":"1"}, json={"authenticationTicket": self.rbx_authentication_ticket}, proxy=proxy)
        set_cookie_header = str(response.cookies.get(".ROBLOSECURITY"))
        assert set_cookie_header, "An error occurred while getting the set_cookie"
        return set_cookie_header.split(".ROBLOSECURITY=")[1].split(";")[0]

        
    async def get_rbx_authentication_ticket(self, session, proxy):
        response = await session.post("https://auth.roblox.com/v1/authentication-ticket", headers={"rbxauthenticationnegotiation":"1", "referer": "https://www.roblox.com/camel", 'Content-Type': 'application/json', "x-csrf-token": self.xcsrf_token}, cookies={".ROBLOSECURITY": self.cookie}, proxy=proxy)
        assert response.headers.get("rbx-authentication-ticket"), "An error occurred while getting the rbx-authentication-ticket"
        return response.headers.get("rbx-authentication-ticket")
        
        
    async def get_csrf_token(self, session, proxy) -> str:
        response = await session.post("https://auth.roblox.com/v2/logout", cookies = {".ROBLOSECURITY": self.cookie}, proxy=proxy)
        xcsrf_token = response.headers.get("x-csrf-token")
        assert xcsrf_token, "An error occurred while getting the X-CSRF-TOKEN. Could be due to an invalid Roblox Cookie"
                 
        return xcsrf_token
    
class RobloxCookie(Bypass):
    def __init__(self, cookie, proxies):
        self.cookie = cookie
        self._x_token = None
        self.proxies = proxies
        self.proxy = random.choice(proxies)
        self.last_generated_time = 120

    async def generate_token(self, session):
        self._x_token = (await session.post("https://economy.roblox.com/", cookies={".ROBLOSECURITY": self.cookie}, proxy=self.proxy)).headers.get("x-csrf-token")
        self.last_generated_time = time.time()

    async def x_token(self, session):
        current_time = time.time()
        if current_time - self.last_generated_time >= 120:
            await self.generate_token(session)
        return self._x_token
    
    async def region_unlock(self, session):
        try:
            self.cookie = await super().run(self.cookie, session, self.proxy)
            print("refreshed cookie")
            return self.cookie
        except:
            print("failed to refresh")
            self.cookie = None
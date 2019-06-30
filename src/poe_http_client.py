from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Callable

import aiohttp
from galaxy.api.errors import AuthenticationRequired
from galaxy.http import HttpClient

from poe_types import PoeSessionId, ProfileName


class PoeHttpClient(HttpClient):
    def __init__(self, poesessid: PoeSessionId, profile_name: ProfileName, auth_lost_callback: Callable):
        self._profile_name = profile_name
        self._auth_lost_callback = auth_lost_callback
        cookies = aiohttp.CookieJar()
        cookies.update_cookies(SimpleCookie("POESESSID={}; Domain=pathofexile.com;".format(poesessid)))
        super().__init__(limit=30, timeout=aiohttp.ClientTimeout(total=30), cookie_jar=cookies)

    async def get_page(self, *args, **kwargs) -> str:
        response = await super().request("GET", *args, allow_redirects=False, **kwargs)
        if response.status == HTTPStatus.FOUND:
            self._auth_lost_callback()
            raise AuthenticationRequired()

        return await response.text(encoding="utf-8", errors="replace")

    async def shutdown(self):
        await super().close()

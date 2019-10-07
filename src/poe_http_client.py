from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Callable

import aiohttp
from aiohttp.client import ClientResponse
from bs4 import BeautifulSoup
from galaxy.api.errors import AuthenticationRequired, UnknownBackendResponse
from galaxy.http import HttpClient

from poe_types import AchievementTagSet, HtmlPage, PoeSessionId, ProfileName


class PoeHttpClient(HttpClient):
    _INSTALL_BIN_URL = "https://www.pathofexile.com/downloads/PathOfExileInstaller.exe"

    def __init__(self, poesessid: PoeSessionId, profile_name: ProfileName, auth_lost_callback: Callable):
        self._profile_name = profile_name
        self._auth_lost_callback = auth_lost_callback
        cookies = aiohttp.CookieJar()
        cookies.update_cookies(SimpleCookie(f"POESESSID={poesessid}; Domain=pathofexile.com;"))
        super().__init__(limit=30, timeout=aiohttp.ClientTimeout(total=30), cookie_jar=cookies)

    async def _authenticated_request(self, method, *args, **kwargs) -> ClientResponse:
        response = await super().request(method, *args, **kwargs)
        if response.status == HTTPStatus.FOUND:
            self._auth_lost_callback()
            raise AuthenticationRequired()

        return response

    async def _get_page(self, *args, **kwargs) -> HtmlPage:
        return HtmlPage(await (
            await self._authenticated_request("GET", *args, allow_redirects=False, **kwargs)
        ).text(encoding="utf-8", errors="replace"))

    async def _get_file(self, *args, **kwargs) -> bytes:
        return await (
            await self._authenticated_request("GET", *args, allow_redirects=False, **kwargs)
        ).read()

    async def get_achievements(self, *args, **kwargs) -> AchievementTagSet:
        response = await self._get_page(
            *args
            , url=f"https://www.pathofexile.com/account/view-profile/{self._profile_name}/achievements"
            , **kwargs)

        try:
            return BeautifulSoup(response, "lxml").select("div.achievement:not(.incomplete)")
        except Exception as e:
            raise UnknownBackendResponse(str(e))

    async def get_installer(self, *args, **kwargs) -> bytes:
        return await self._get_file(*args, url=self._INSTALL_BIN_URL, **kwargs)

    async def shutdown(self):
        await super().close()

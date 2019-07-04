import json
import os
import re
import sys
from typing import Dict, List, NewType, Optional, Union

from galaxy.api.consts import Platform
from galaxy.api.errors import InvalidCredentials
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.types import Authentication, NextStep

PoeSessionId = NewType("PoeSessionId", str)
ProfileName = NewType("ProfileName", str)


class PoePlugin(Plugin):
    _AUTH_REDIRECT = r"https://localhost/poe?name="
    _AUTH_SESSION_ID = "POESESSID"
    _AUTH_PROFILE_NAME = "PROFILE_NAME"

    @staticmethod
    def _read_manifest():
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")) as manifest:
            return json.load(manifest)

    def __init__(self, reader, writer, token):
        self._manifest = self._read_manifest()
        super().__init__(Platform(self._manifest["platform"]), self._manifest["version"], reader, writer, token)

    async def _do_auth(
        self, poesessid: PoeSessionId, profile_name: ProfileName, store_poesessid: bool = True
    ) -> Authentication:
        if not poesessid:
            raise InvalidCredentials(self._AUTH_SESSION_ID)
        if not profile_name:
            raise InvalidCredentials(self._AUTH_PROFILE_NAME)

        if store_poesessid:
            self.store_credentials({self._AUTH_SESSION_ID: poesessid, self._AUTH_PROFILE_NAME: profile_name})

        return Authentication(user_id=profile_name, user_name=profile_name)

    async def authenticate(self, stored_credentials: dict = None) -> Union[Authentication, NextStep]:
        poesessid: Optional[PoeSessionId] = None
        profile_name: Optional[ProfileName] = None

        if stored_credentials:
            poesessid = stored_credentials.get(self._AUTH_SESSION_ID)
            profile_name = stored_credentials.get(self._AUTH_PROFILE_NAME)

        if poesessid and profile_name:
            return await self._do_auth(poesessid, profile_name, store_poesessid=False)

        return NextStep(
            "web_session"
            , {
                "window_title": "Still sane, exile?"
                , "window_width": 800
                , "window_height": 600
                , "start_uri": "https://www.pathofexile.com/login"
                , "end_uri_regex": re.escape(self._AUTH_REDIRECT) + ".*"
            }
            , js={
                "https://www.pathofexile.com/my-account": [
                    r'''
                        profileName = document.getElementsByClassName("name")[0].textContent;
                        window.location.replace("''' + self._AUTH_REDIRECT + r'''" + profileName);
                    '''
                ]
            }
        )

    async def pass_login_credentials(self, step: str, credentials: Dict[str, str], cookies: List[Dict[str, str]]):
        def get_session_id() -> PoeSessionId:
            for c in cookies:
                if c.get("name") == self._AUTH_SESSION_ID and c.get("value"):
                    return PoeSessionId(c["value"])

            raise InvalidCredentials(self._AUTH_SESSION_ID + "not found in cookies")

        def get_profile_name() -> ProfileName:
            split_uri = credentials["end_uri"].split(self._AUTH_REDIRECT, maxsplit=1)
            if not split_uri or len(split_uri) < 2:
                raise InvalidCredentials(self._AUTH_PROFILE_NAME + " not found")
            return ProfileName(split_uri[1])

        return await self._do_auth(get_session_id(), get_profile_name())


def main():
    create_and_run_plugin(PoePlugin, sys.argv)


if __name__ == "__main__":
    main()

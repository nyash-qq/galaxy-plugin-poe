import asyncio
import json
import os
import platform
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union

import psutil
from galaxy.api.consts import Platform
from galaxy.api.errors import (
    ApplicationError, AuthenticationRequired, InvalidCredentials, UnknownBackendResponse, UnknownError,
)
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.types import (
    Achievement, Authentication, Game, LicenseInfo, LicenseType, LocalGame, LocalGameState, NextStep
)

from poe_http_client import PoeHttpClient
from poe_types import AchievementName, AchievementTag, PoeSessionId, ProfileName, Timestamp


def is_windows() -> bool:
    return platform.system() == "Windows"


if is_windows():
    import winreg


class PoePlugin(Plugin):
    VERSION = "0.1"

    _AUTH_REDIRECT = r"https://localhost/poe?name="
    _AUTH_SESSION_ID = "POESESSID"
    _AUTH_PROFILE_NAME = "PROFILE_NAME"

    @staticmethod
    def _read_manifest():
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")) as manifest:
            return json.load(manifest)

    _GAME_ID = "PathOfExile"
    _GAME_BIN = "PathOfExile_x64.exe" if is_windows() else ""
    _PROC_NAMES = ["pathofexile.exe", "pathofexile_x64.exe"] if is_windows() else []

    def __init__(self, reader, writer, token):
        self._http_client: Optional[PoeHttpClient] = None
        self._install_path: Optional[str] = self._get_install_path()
        self._game_state: LocalGameState = self._get_game_state()
        self._manifest = self._read_manifest()
        self._achievements_cache: Dict[AchievementName, Timestamp] = {}
        super().__init__(Platform(self._manifest["platform"]), self._manifest["version"], reader, writer, token)

    def _close_client(self):
        if not self._http_client:
            return

        asyncio.create_task(self._http_client.shutdown())
        self._http_client = None

    def _on_auth_lost(self):
        self._close_client()
        self.lost_authentication()

    async def _do_auth(
        self, poesessid: PoeSessionId, profile_name: ProfileName, store_poesessid: bool = True
    ) -> Authentication:
        if not poesessid:
            raise InvalidCredentials(self._AUTH_SESSION_ID)
        if not profile_name:
            raise InvalidCredentials(self._AUTH_PROFILE_NAME)

        self._http_client = PoeHttpClient(poesessid, profile_name, self._on_auth_lost)

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

    async def get_owned_games(self) -> List[Game]:
        return [Game(
            game_id=self._GAME_ID
            , game_title="Path of Exile"
            , dlcs=[]
            , license_info=LicenseInfo(LicenseType.FreeToPlay)
        )]

    # TODO: remove when galaxy.api's feature detection is fixed
    async def get_unlocked_achievements(self, game_id: str) -> List[Achievement]:
        return []

    async def start_achievements_import(self, game_ids: List[str]) -> None:
        if not self._http_client:
            raise AuthenticationRequired()

        await super().start_achievements_import(game_ids)

    async def import_games_achievements(self, game_ids: List[str]) -> None:
        try:
            def achievement_parser(achievement_tag: Optional[AchievementTag]) -> Achievement:
                achievement_name = achievement_tag.h2.get_text()
                if not achievement_name:
                    raise UnknownBackendResponse("Failed to parse achievement name")

                return Achievement(
                    unlock_time=self._achievements_cache.setdefault(
                        achievement_name
                        , Timestamp(int(datetime.utcnow().timestamp()))
                    )
                    , achievement_name=achievement_name
                )

            self.game_achievements_import_success(
                self._GAME_ID
                , [
                    achievement_parser(achievement_tag)
                    for achievement_tag in await self._http_client.get_achievements()
                ]
            )
        except ApplicationError as e:
            self.game_achievements_import_failure(self._GAME_ID, e)
        except AttributeError as e:
            self.game_achievements_import_failure(self._GAME_ID, UnknownBackendResponse(str(e)))
        except Exception as e:
            self.game_achievements_import_failure(self._GAME_ID, UnknownError(str(e)))

    if is_windows():
        def tick(self):
            if not self._install_path:
                self._install_path = self._get_install_path()

            current_game_state = self._get_game_state()
            if self._game_state != current_game_state:
                self._game_state = current_game_state
                self.update_local_game_status(LocalGame(self._GAME_ID, self._game_state))

        @staticmethod
        def _get_install_path() -> Optional[str]:
            if not is_windows():
                return None

            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\GrindingGearGames\Path of Exile") as h_key:
                    return winreg.QueryValueEx(h_key, "InstallLocation")[0]

            except (WindowsError, ValueError):
                return None

        def _is_installed(self) -> bool:
            if not self._install_path:
                return False

            return (
                os.path.exists(os.path.join(self._install_path, self._GAME_BIN))
                and os.path.exists(os.path.join(self._install_path, "Content.ggpk"))
            )

        def _is_running(self) -> bool:
            for proc in psutil.process_iter():
                if proc.name().lower() in self._PROC_NAMES:
                    return True

            return False

        def _get_game_state(self) -> LocalGameState:
            if not self._is_installed():
                return LocalGameState.None_

            if self._is_running():
                return LocalGameState.Running

            return LocalGameState.Installed

        async def get_local_games(self) -> List[LocalGame]:
            self._game_state = self._get_game_state()
            return [LocalGame(self._GAME_ID, self._game_state)]

    def shutdown(self):
        self._close_client()


def main():
    create_and_run_plugin(PoePlugin, sys.argv)


if __name__ == "__main__":
    main()

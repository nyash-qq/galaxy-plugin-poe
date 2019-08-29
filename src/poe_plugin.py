import asyncio
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Union

import aiofiles
import psutil
from galaxy.api.consts import Platform
from galaxy.api.errors import (
    AuthenticationRequired, InvalidCredentials, UnknownBackendResponse,
)
from galaxy.api.plugin import create_and_run_plugin, Plugin
from galaxy.api.types import (
    Achievement, Authentication, Game, LicenseInfo, LicenseType, LocalGame, LocalGameState, NextStep
)

from poe_http_client import AchievementTagSet, PoeHttpClient
from poe_types import AchievementName, AchievementTag, PoeSessionId, ProfileName, Timestamp


def is_windows() -> bool:
    return platform.system() == "Windows"


if is_windows():
    import winreg


class PoePlugin(Plugin):
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

    _INSTALLER_BIN = "PathOfExileInstaller.exe"

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

    def requires_authentication(self):
        if not self._http_client:
            raise AuthenticationRequired()

    async def prepare_achievements_context(self, game_ids: List[str]) -> AchievementTagSet:
        self.requires_authentication()

        return await self._http_client.get_achievements()

    async def get_unlocked_achievements(self, game_id: str, achievement_tags: AchievementTagSet) -> List[Achievement]:
        def achievement_parser(achievement_tag: Optional[AchievementTag]) -> Achievement:
            name_tag = achievement_tag.h2
            if not name_tag:
                raise UnknownBackendResponse("Cannot find achievement name tag")

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

        return [
            achievement_parser(achievement_tag)
            for achievement_tag in achievement_tags
        ]

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

        @staticmethod
        def _exec(command_path: str, *args, arg: List[str] = None, **kwargs):
            subprocess.Popen(
                [command_path] + (arg if arg else [])
                , *args
                , creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
                , cwd=os.path.dirname(command_path)
                , **kwargs
            )

        async def launch_game(self, game_id: str):
            if self._install_path:
                self._exec(os.path.join(self._install_path, self._GAME_BIN))

        async def _get_installer(self) -> str:
            def get_cached() -> Optional[str]:
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                    ) as h_info_root:
                        for idx in range(winreg.QueryInfoKey(h_info_root)[0]):
                            try:
                                with winreg.OpenKeyEx(h_info_root, winreg.EnumKey(h_info_root, idx)) as h_sub_node:
                                    def get_value(key):
                                        return winreg.QueryValueEx(h_sub_node, key)[0]

                                    if get_value("DisplayName") == "Path of Exile" and get_value("Installed"):
                                        installer_path = get_value("BundleCachePath")
                                        if os.path.exists(str(installer_path)):
                                            return installer_path

                            except (WindowsError, KeyError, ValueError):
                                continue

                except (WindowsError, KeyError, ValueError):
                    return None

            async def download():
                self.requires_authentication()

                installer_path = os.path.join(tempfile.mkdtemp(), self._INSTALLER_BIN)
                async with aiofiles.open(installer_path, mode="wb") as installer_bin:
                    await installer_bin.write(await self._http_client.get_installer())

                return installer_path

            return get_cached() or await download()

        async def install_game(self, game_id: str):
            self._exec(await self._get_installer())

        async def uninstall_game(self, game_id: str):
            self._exec(await self._get_installer(), arg=["/uninstall"])

    def shutdown(self):
        self._close_client()


def main():
    create_and_run_plugin(PoePlugin, sys.argv)


if __name__ == "__main__":
    main()

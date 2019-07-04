import asyncio
from unittest.mock import MagicMock

import pytest

from poe_plugin import PoePlugin, PoeSessionId, ProfileName


@pytest.fixture()
def manifest_mock(mocker):
    return mocker.patch("poe_plugin.PoePlugin._read_manifest")


@pytest.fixture()
def poesessid() -> PoeSessionId:
    return PoeSessionId("poesessid")


@pytest.fixture()
def profile_name() -> ProfileName:
    return ProfileName("profile_name")


@pytest.fixture()
def stored_credentials(poesessid, profile_name) -> dict:
    return {PoePlugin._AUTH_SESSION_ID: poesessid, PoePlugin._AUTH_PROFILE_NAME: profile_name}


@pytest.fixture()
async def poe_plugin_mock(manifest_mock):
    manifest_mock.return_value = {
        "name": "Galaxy Poe plugin"
        , "platform": "pathofexile"
        , "guid": "52d06761-1c23-d725-9720-57ee0b8b14bc"
        , "version": "0.1"
        , "description": "Galaxy Poe plugin"
        , "author": "nyash"
        , "email": "nyash.qq@gmail.com"
        , "url": "https://github.com/nyash-qq/galaxy-plugin-poe"
        , "script": "poe_plugin.py"
    }

    instance = PoePlugin(MagicMock(), MagicMock(), "handshake_token")
    yield instance

    instance.shutdown()
    await asyncio.sleep(0)

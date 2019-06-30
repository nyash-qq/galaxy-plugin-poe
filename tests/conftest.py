import asyncio
from unittest.mock import ANY, MagicMock

import pytest

from poe_plugin import PoeHttpClient, PoePlugin
from poe_types import PoeSessionId, ProfileName
from tests.utils import AsyncMock

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
def http_client_mock(mocker):
    return mocker.patch("poe_plugin.PoeHttpClient", return_value=MagicMock(spec=()))


@pytest.fixture()
async def mock_http_client(http_client_mock, poesessid, profile_name) -> PoeHttpClient:
    http_client = http_client_mock.return_value
    http_client.shutdown = AsyncMock()
    yield http_client

    http_client_mock.assert_called_once_with(poesessid, profile_name, ANY)
    http_client.shutdown.assert_called_once_with()


@pytest.fixture()
def poe_plugin_mock(manifest_mock) -> PoePlugin:
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
    return PoePlugin(MagicMock(), MagicMock(), "handshake_token")


@pytest.fixture()
async def poe_plugin(poe_plugin_mock) -> PoePlugin:
    yield poe_plugin_mock

    poe_plugin_mock.shutdown()
    await asyncio.sleep(0)

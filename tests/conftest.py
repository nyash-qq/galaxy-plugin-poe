import asyncio
from unittest.mock import MagicMock

import pytest

from poe_plugin import PoePlugin, PoeSessionId, ProfileName


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
async def poe_plugin_mock():
    instance = PoePlugin(MagicMock(), MagicMock(), "handshake_token")
    yield instance

    instance.shutdown()
    await asyncio.sleep(0)

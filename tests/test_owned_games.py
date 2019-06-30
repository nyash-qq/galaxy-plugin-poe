import pytest

from galaxy.api.types import Game, LicenseInfo, LicenseType


@pytest.fixture()
def poe_game():
    return Game(
        game_id="PathOfExile"
        , game_title="Path of Exile"
        , dlcs=[]
        , license_info=LicenseInfo(license_type=LicenseType.FreeToPlay)
    )


@pytest.mark.asyncio
async def test_get_owned_games(
    poe_plugin
    , poe_game
):
    assert [poe_game] == await poe_plugin.get_owned_games()

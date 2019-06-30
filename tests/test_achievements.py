import asyncio
from datetime import datetime
from unittest.mock import ANY

import pytest
from galaxy.api.errors import UnknownBackendResponse
from galaxy.api.types import Achievement

from tests.utils import AsyncMock, MagicMock

_ACHIEVEMENTS_PAGE = '''
<html>
    <body>
        <div class="achievement-list">
            <div class="achievement clearfix"><a class="btn-detail"></a>
                <h2>Shaper of Worlds</h2>
                <div class="detail">
                    <span class="text">Defeat the Shaper.</span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png"/>
            </div>
            <div class="achievement clearfix incomplete"><a class="btn-detail expanded"></a>
                <h2>Breachlord</h2>
                <h2 class="completion-detail"><span class="completion-incomplete">4</span>/5</h2>
                <div class="detail" style="display: block;">
                    <span class="text">Kill every Breachlord.</span><br/><br/>
                    <span class="items">
                        <ul class="split">
                            <li class="finished">Esh, Forked Thought</li>
                            <li class="finished">Tul, Creeping Avalanche</li>
                            <li class="finished">Uul-Netol, Unburdened Flesh</li>
                        </ul>
                        <ul class="split">
                            <li class="finished">Xoph, Dark Embers</li>
                            <li class="">Chayula, Who Dreamt</li>
                        </ul>
                    </span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Cross.png?hash=edf6a81e4c9ce92681d0ca95b757bb27"/>
            </div>
            <div class="achievement clearfix"><a class="btn-detail"></a>
                <h2>New World Order</h2>
                <div class="detail">
                    <span class="text">Upgrade a map with a Shaper's Orb.</span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
            </div>
            <div class="achievement clearfix"><a class="btn-detail"></a>
                <h2>Sacrifice of the Vaal</h2>
                <div class="detail">
                    <span class="text">Kill Atziri in the Alluring Abyss.</span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
            </div>
            <div class="achievement clearfix incomplete"><a class="btn-detail"></a>
                <h2>Grandmaster</h2>
                <div class="detail">
                    <span class="text">Complete the Hall of Grandmasters.</span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Cross.png?hash=edf6a81e4c9ce92681d0ca95b757bb27"/>
            </div>
            <div class="achievement clearfix"><a class="btn-detail"></a>
                <h2>Unforgettable</h2>
                <h2 class="completion-detail"><span class="">15</span>/15</h2>
                <div class="detail">
                <span class="text">Obtain the Shaper's Memory Fragments I through XV.</span><br/><br/>
                <span class="items">
                    <ul class="split">
                        <li class="finished">Memory Fragment I</li>
                        <li class="finished">Memory Fragment II</li>
                        <li class="finished">Memory Fragment III</li>
                        <li class="finished">Memory Fragment IV</li>
                        <li class="finished">Memory Fragment V</li>
                        <li class="finished">Memory Fragment VI</li>
                        <li class="finished">Memory Fragment VII</li>
                        <li class="finished">Memory Fragment VIII</li>
                    </ul>
                    <ul class="split">
                        <li class="finished">Memory Fragment IX</li>
                        <li class="finished">Memory Fragment X</li>
                        <li class="finished">Memory Fragment XI</li>
                        <li class="finished">Memory Fragment XII</li>
                        <li class="finished">Memory Fragment XIII</li>
                        <li class="finished">Memory Fragment XIV</li>
                        <li class="finished">Memory Fragment XV</li>
                    </ul>
                </span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
            </div>
            <div class="achievement clearfix"><a class="btn-detail"></a>
                <h2>Augmentation</h2>
                <div class="detail">
                    <span class="text">Use an orb to change the mods of a Strongbox.</span>
                </div>
                <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
            </div>
        </div>
    </body>
</html>
'''

_UNLOCK_DATE = datetime(year=2019, month=2, day=7)
_UNLOCK_TIMESTAMP = 1549494000
_UNLOCKED_ACHIEVEMENTS = [
    Achievement(_UNLOCK_TIMESTAMP, achievement_name=name)
    for name in ("Shaper of Worlds", "New World Order", "Sacrifice of the Vaal", "Unforgettable")
]


@pytest.fixture()
def get_page_mock(mocker):
    return mocker.patch("poe_plugin.PoeHttpClient._get_page", new_callable=AsyncMock)


@pytest.fixture()
def date_time_mock(mocker):
    dt_mock = mocker.patch("poe_plugin.datetime")
    dt_mock.utcnow = MagicMock(return_value=_UNLOCK_DATE)
    return dt_mock


@pytest.fixture()
def import_success_mock(mocker):
    return mocker.patch("poe_plugin.PoePlugin.game_achievements_import_success")


@pytest.fixture()
def import_failed_mock(mocker):
    return mocker.patch("poe_plugin.PoePlugin.game_achievements_import_failure")


@pytest.mark.asyncio
@pytest.mark.parametrize("backend_response, achievements, cached_achievement", [
    ("", [], None)
    , ("<div class=\"achievement-list\"></div>", [], None)
    , (_ACHIEVEMENTS_PAGE, _UNLOCKED_ACHIEVEMENTS, Achievement(1548111600, achievement_name="Augmentation"))
    , (_ACHIEVEMENTS_PAGE, _UNLOCKED_ACHIEVEMENTS, Achievement(_UNLOCK_DATE, achievement_name="Augmentation"))
])
async def test_import_achievements_success(
    backend_response
    , achievements
    , cached_achievement
    , get_page_mock
    , import_success_mock
    , import_failed_mock
    , auth_poe_plugin
    , game_id
    , date_time_mock
):
    get_page_mock.return_value = backend_response
    if cached_achievement:
        auth_poe_plugin._achievements_cache[cached_achievement.achievement_name] = cached_achievement.unlock_time

    await auth_poe_plugin.start_achievements_import([game_id])
    await asyncio.sleep(0)

    import_success_mock.assert_called_once_with(
        game_id
        , achievements + [cached_achievement] if cached_achievement else []
    )
    import_failed_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("backend_response", [
    '''<div class="achievement-list">
    <div class="achievement clearfix"><a class="btn-detail"></a>
        <h2></h2>
        <div class="detail">
            <span class="text">Defeat the Shaper.</span>
        </div>
        <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png"/>
    </div>
    </div>'''
    , '''<div class="achievement-list">
    <div class="achievement clearfix"><a class="btn-detail"></a>
        <div class="detail">
            <span class="text">Defeat the Shaper.</span>
        </div>
        <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png"/>
    </div>
    </div>'''
])
async def test_import_achievements_failure(
    backend_response
    , get_page_mock
    , import_success_mock
    , import_failed_mock
    , auth_poe_plugin
    , game_id
    , date_time_mock
):
    get_page_mock.return_value = backend_response

    await auth_poe_plugin.start_achievements_import([game_id])
    await asyncio.sleep(0)

    import_success_mock.assert_not_called()
    import_failed_mock.assert_called_once_with(game_id, ANY)
    assert type(import_failed_mock.call_args[0][1]) is UnknownBackendResponse

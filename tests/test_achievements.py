from datetime import datetime

import pytest
from bs4 import BeautifulSoup
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
_UNLOCKED_ACHIEVEMENTS_TAGS = [
    BeautifulSoup(tag, "lxml").div for tag in (
        '''<div class="achievement clearfix"><a class="btn-detail"></a>
            <h2>Shaper of Worlds</h2>
            <div class="detail">
                <span class="text">Defeat the Shaper.</span>
            </div>
            <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png"/>
        </div>'''
        , '''<div class="achievement clearfix"><a class="btn-detail"></a>
            <h2>New World Order</h2>
            <div class="detail">
                <span class="text">Upgrade a map with a Shaper's Orb.</span>
            </div>
            <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
        </div>'''
        , '''<div class="achievement clearfix"><a class="btn-detail"></a>
            <h2>Sacrifice of the Vaal</h2>
            <div class="detail">
                <span class="text">Kill Atziri in the Alluring Abyss.</span>
            </div>
            <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
        </div>'''
        , '''<div class="achievement clearfix"><a class="btn-detail"></a>
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
        </div>'''
        , '''<div class="achievement clearfix"><a class="btn-detail"></a>
            <h2>Augmentation</h2>
            <div class="detail">
                <span class="text">Use an orb to change the mods of a Strongbox.</span>
            </div>
            <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png?hash=1f20be360c2bcbcdafcd6a783ed7a944"/>
        </div>'''
    )
]
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


@pytest.mark.asyncio
@pytest.mark.parametrize("backend_response, achievement_tags", [
    ("", [])
    , ("<div class=\"achievement-list\"></div>", [])
    , (_ACHIEVEMENTS_PAGE, _UNLOCKED_ACHIEVEMENTS_TAGS)
])
async def test_get_achievements_tags(
    backend_response
    , achievement_tags
    , get_page_mock
    , auth_poe_plugin
    , game_id
    , date_time_mock
):
    get_page_mock.return_value = backend_response

    assert await auth_poe_plugin.prepare_achievements_context([game_id]) == achievement_tags


@pytest.mark.asyncio
@pytest.mark.parametrize("achievements_tags, achievements, cached_achievement", [
    ([], [], None)
    , (_UNLOCKED_ACHIEVEMENTS_TAGS, _UNLOCKED_ACHIEVEMENTS, Achievement(1548111600, achievement_name="Augmentation"))
    , (_UNLOCKED_ACHIEVEMENTS_TAGS, _UNLOCKED_ACHIEVEMENTS, Achievement(_UNLOCK_DATE, achievement_name="Augmentation"))
])
async def test_import_achievements_success(
    achievements_tags
    , achievements
    , cached_achievement
    , auth_poe_plugin
    , game_id
    , date_time_mock
):
    unlocked_achievements = achievements[:]

    if cached_achievement is not None:
        auth_poe_plugin._achievements_cache[cached_achievement.achievement_name] = cached_achievement.unlock_time
        unlocked_achievements.append(cached_achievement)

    assert await auth_poe_plugin.get_unlocked_achievements(
        game_id, achievements_tags
    ) == unlocked_achievements


@pytest.mark.asyncio
@pytest.mark.parametrize("achievement_tag", [
    BeautifulSoup(tag, "lxml").div for tag in (
        '''<div class="achievement clearfix"><a class="btn-detail"></a>
            <h2></h2>
            <div class="detail">
                <span class="text">Defeat the Shaper.</span>
            </div>
            <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png"/>
        </div>'''
        , '''<div class="achievement clearfix"><a class="btn-detail"></a>
            <div class="detail">
                <span class="text">Defeat the Shaper.</span>
            </div>
            <img class="completion" src="https://web.poecdn.com/image/Art/2DArt/UIImages/InGame/Tick.png"/>
        </div>'''
    )])
async def test_import_achievements_failure(
    achievement_tag
    , auth_poe_plugin
    , game_id
    , date_time_mock
):
    with pytest.raises(UnknownBackendResponse):
        assert await auth_poe_plugin.get_unlocked_achievements(game_id, [achievement_tag])

import pytest
from galaxy.api.errors import InvalidCredentials
from galaxy.api.types import Authentication, NextStep


@pytest.fixture()
def auth_info(profile_name):
    return Authentication(profile_name, profile_name)


@pytest.fixture()
def store_credentials_mock(mocker):
    return mocker.patch("poe_plugin.PoePlugin.store_credentials")


@pytest.fixture()
def lost_authentication_mock(mocker):
    return mocker.patch("poe_plugin.PoePlugin.lost_authentication")


@pytest.mark.asyncio
async def test_auth_no_stored_credentials(
    poe_plugin_mock
    , store_credentials_mock
    , auth_info
    , profile_name
    , poesessid
    , stored_credentials
):
    assert type(await poe_plugin_mock.authenticate(None)) is NextStep

    assert auth_info == await poe_plugin_mock.pass_login_credentials(
        "step", {"end_uri": poe_plugin_mock._AUTH_REDIRECT + profile_name}, [{"name": "POESESSID", "value": poesessid}]
    )

    store_credentials_mock.assert_called_once_with(stored_credentials)


@pytest.mark.asyncio
async def test_auth_stored_credentials(
    poe_plugin_mock
    , store_credentials_mock
    , auth_info
    , stored_credentials
):
    assert auth_info == await poe_plugin_mock.authenticate(stored_credentials)
    store_credentials_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_params", [
    ("step", {}, [])
    , ("step", {"end_uri": "bad-uri"}, [{"name": "POESESSID", "value": "poesessid"}])
    , ("step", {"end_uri": "https://localhost/poe?name="}, [{"name": "POESESSID", "value": "poesessid"}])
    , ("step", {"end_uri": "https://localhost/poe?name=profile_name"}, [{"name": "other-cookie", "value": "poesessid"}])
    , ("step", {"end_uri": "https://localhost/poe?name=profile_name"}, [{"name": "POESESSID", "value": None}])
])
async def test_auth_failed_no_credentials(
    auth_params
    , poe_plugin_mock
):
    with pytest.raises(InvalidCredentials):
        assert await poe_plugin_mock.pass_login_credentials(*auth_params)

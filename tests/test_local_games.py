import platform
import subprocess

if platform.system() == "Windows":
    import os
    import winreg
    from unittest.mock import MagicMock, call

    import pytest
    from galaxy.api.types import LocalGame, LocalGameState

    from poe_plugin import PoePlugin


    def proc_mock(name):
        proc = MagicMock(spec=())
        proc.binary_path = name
        return proc


    _PROCESS_LIST_NOT_RUNNING = [
        proc_mock(name)
        for name in ("c:\\opera.exe", "d:\\GalaxyClient.exe", "d:\\PathOfExile not game.exe", "e:\\not PathOfExile.exe")
    ]
    _PROCESS_LIST_RUNNING = [
        proc_mock(name)
        for name in ("c:\\opera.exe", "d:\\GalaxyClient.exe", "d:\\PathOfExile_x64.exe")
    ]

    _GAME_BIN = PoePlugin._GAME_BIN
    _GAME_ID = PoePlugin._GAME_ID
    _GAME_STATE_NOT_INSTALLED = LocalGame(_GAME_ID, LocalGameState.None_)
    _GAME_STATE_INSTALLED = LocalGame(_GAME_ID, LocalGameState.Installed)
    _GAME_STATE_RUNNING = LocalGame(_GAME_ID, LocalGameState.Running)


    @pytest.fixture()
    def path_exists_mock(mocker):
        return mocker.patch("poe_plugin.os.path.exists")


    @pytest.fixture()
    def process_iter_mock(mocker):
        return mocker.patch("poe_plugin.process_iter")


    @pytest.fixture()
    def process_open_mock(mocker):
        return mocker.patch("subprocess.Popen")


    @pytest.mark.asyncio
    @pytest.mark.parametrize("install_path, is_installed, process_list, game_state", [
        (None, False, [], _GAME_STATE_NOT_INSTALLED)
        , ("installed", False, [], _GAME_STATE_NOT_INSTALLED)
        , ("installed", True, _PROCESS_LIST_NOT_RUNNING, _GAME_STATE_INSTALLED)
        , ("installed", True, _PROCESS_LIST_RUNNING, _GAME_STATE_RUNNING)
    ])
    async def test_get_game_state(
        install_path
        , is_installed
        , process_list
        , game_state
        , poe_plugin
        , game_id
        , path_exists_mock
        , process_iter_mock
    ):
        poe_plugin._install_path = install_path
        path_exists_mock.return_value = is_installed
        process_iter_mock.return_value = process_list

        assert [game_state] == await poe_plugin.get_local_games()
        if is_installed:
            process_iter_mock.assert_called_once_with()
        if install_path and is_installed:
            path_exists_mock.assert_has_calls(
                [call(os.path.join(install_path, _GAME_BIN))
                    , call(os.path.join(install_path, "Content.ggpk"))]
                , any_order=True
            )


    @pytest.mark.asyncio
    @pytest.mark.parametrize("install_path, is_installed, process_list, game_state", [
        (None, False, [], _GAME_STATE_NOT_INSTALLED)
        , ("installed", False, [], _GAME_STATE_NOT_INSTALLED)
        , ("installed", True, _PROCESS_LIST_NOT_RUNNING, _GAME_STATE_INSTALLED)
        , ("installed", True, _PROCESS_LIST_RUNNING, _GAME_STATE_RUNNING)
    ])
    async def test_game_state_update(
        install_path
        , is_installed
        , process_list
        , game_state
        , poe_plugin
        , game_id
        , reg_query_value_mock
        , path_exists_mock
        , process_iter_mock
        , mocker
    ):
        if not is_installed:
            poe_plugin._install_path = "previous_location"
            poe_plugin._game_state = LocalGameState.Installed

        reg_query_value_mock.return_value = (install_path, winreg.REG_SZ)
        path_exists_mock.return_value = is_installed
        process_iter_mock.return_value = process_list
        game_state_update_mock = mocker.patch("poe_plugin.PoePlugin.update_local_game_status")

        poe_plugin.tick()

        game_state_update_mock.assert_called_once_with(game_state)
        if is_installed:
            process_iter_mock.assert_called_once_with()

        if install_path:
            if is_installed:
                path_exists_mock.assert_has_calls(
                    [call(os.path.join(install_path, _GAME_BIN))
                        , call(os.path.join(install_path, "Content.ggpk"))]
                    , any_order=True
                )


    @pytest.mark.asyncio
    @pytest.mark.parametrize("install_path", [None, "path"])
    async def test_launch_game(
        install_path
        , poe_plugin
        , process_open_mock
    ):
        poe_plugin._install_path = install_path
        await poe_plugin.launch_game(_GAME_ID)
        if install_path:
            process_open_mock.assert_called_once_with(
                [os.path.join(install_path, "PathOfExile_x64.exe")],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                cwd=install_path
            )
        else:
            process_open_mock.assert_not_called()

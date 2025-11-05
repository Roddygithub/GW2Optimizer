import pytest
import httpx
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock, call
from app.services.gw2_api import GW2APIService


@pytest.fixture
async def gw2_api():
    # Créer une instance de GW2APIService avec un client mock
    api = GW2APIService(api_key="test_api_key")
    # On mock _make_request au lieu de client
    api._make_request = AsyncMock()
    yield api
    await api.close()


@pytest.mark.asyncio
async def test_get_wvw_matches(gw2_api):
    # Configurer la réponse simulée - l'API GW2 renvoie directement un tableau de matchs
    mock_response = [{"id": "1-1", "worlds": {"red": 1001, "blue": 1002, "green": 1003}}]
    gw2_api._make_request.return_value = mock_response

    # Appeler la méthode à tester
    result = await gw2_api.get_wvw_matches(world_id=1001)

    # Vérifier les résultats
    assert result == mock_response

    # Vérifier que _make_request a été appelé avec les bons arguments
    gw2_api._make_request.assert_called_once()
    args, kwargs = gw2_api._make_request.call_args
    assert args[0] == "/wvw/matches"  # endpoint
    if "params" in kwargs and kwargs["params"] is not None:
        assert kwargs["params"] == {"world": 1001}  # params
    assert kwargs.get("authenticated", False) is False  # authenticated


@pytest.mark.asyncio
async def test_get_wvw_match_details(gw2_api):
    # Configurer la réponse simulée
    match_id = "1-1"
    mock_response = {"id": match_id, "scores": {"red": 100, "blue": 200, "green": 150}}
    gw2_api._make_request.return_value = mock_response

    # Appeler la méthode à tester
    result = await gw2_api.get_wvw_match_details(match_id)

    # Vérifier les résultats
    assert result == mock_response

    # Vérifier que _make_request a été appelé avec les bons arguments
    gw2_api._make_request.assert_called_once()
    args, kwargs = gw2_api._make_request.call_args
    assert args[0] == f"/wvw/matches/{match_id}"  # endpoint
    assert kwargs.get("params") is None  # params doit être None
    assert kwargs.get("authenticated", False) is False  # authenticated doit être False


@pytest.mark.asyncio
async def test_get_wvw_objectives(gw2_api):
    # Configurer la réponse simulée
    mock_response = [{"id": "red_keep", "name": "Red Keep"}]
    gw2_api._make_request.return_value = mock_response

    # Appeler la méthode à tester
    result = await gw2_api.get_wvw_objectives()

    # Vérifier les résultats
    assert result == mock_response

    # Vérifier que _make_request a été appelé avec les bons arguments
    gw2_api._make_request.assert_called_once()
    args, kwargs = gw2_api._make_request.call_args
    assert args[0] == "/wvw/objectives"  # endpoint
    assert kwargs.get("params") is None  # params doit être None
    assert kwargs.get("authenticated", False) is False  # authenticated doit être False


@pytest.mark.asyncio
async def test_fetch_live_wvw_data_success(gw2_api):
    # Configurer les réponses simulées
    matches = [{"id": "1-1", "worlds": {"red": 1001, "blue": 1002, "green": 1003}}]
    match_details = {"id": "1-1", "scores": {"red": 100, "blue": 200, "green": 150}}
    objectives = [{"id": "red_keep", "name": "Red Keep"}]

    # Configurer les retours successifs de _make_request
    gw2_api._make_request.side_effect = [matches, match_details, objectives]

    # Appeler la méthode à tester
    result = await gw2_api.fetch_live_wvw_data(world_id=1001)

    # Vérifier les résultats
    assert result["status"] == "success"
    assert result["world_id"] == 1001
    assert result["matches"] == matches
    assert result["match_details"] == match_details
    assert result["objectives"] == objectives
    assert "timestamp" in result

    # Vérifier que les appels ont été faits dans le bon ordre
    assert gw2_api._make_request.call_count == 3

    # Vérifier le premier appel (get_wvw_matches)
    args1, kwargs1 = gw2_api._make_request.call_args_list[0]
    assert args1[0] == "/wvw/matches"
    assert kwargs1.get("params") == {"world": 1001}
    assert kwargs1.get("authenticated", False) is False

    # Vérifier le deuxième appel (get_wvw_match_details)
    args2, kwargs2 = gw2_api._make_request.call_args_list[1]
    assert args2[0] == "/wvw/matches/1-1"
    assert kwargs2.get("params") is None
    assert kwargs2.get("authenticated", False) is False

    # Vérifier le troisième appel (get_wvw_objectives)
    args3, kwargs3 = gw2_api._make_request.call_args_list[2]
    assert args3[0] == "/wvw/objectives"
    assert kwargs3.get("params") is None
    assert kwargs3.get("authenticated", False) is False

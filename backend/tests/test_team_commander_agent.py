"""Tests unitaires pour TeamCommanderAgent."""

import pytest

from app.agents.team_commander_agent import TeamCommanderAgent, Role


class TestTeamCommanderAgentParsing:
    """Tests de parsing de requêtes naturelles."""

    def test_parse_request_by_roles(self) -> None:
        agent = TeamCommanderAgent()
        message = (
            "Je veux une équipe de 10 joueurs pour WvW. "
            "Dans chaque groupe il me faut un stabeur, un healer, un booner, "
            "un dps strip et un dps pur."
        )

        req = agent._parse_request(message)  # type: ignore[attr-defined]

        assert req.team_size == 10
        assert req.groups == 2
        # Au moins les 5 rôles de base
        assert Role.STAB in req.roles_per_group
        assert Role.HEAL in req.roles_per_group
        assert Role.BOON in req.roles_per_group
        assert Role.STRIP in req.roles_per_group
        assert Role.DPS in req.roles_per_group
        # Pas de contraintes explicites de classes dans ce cas
        assert req.constraints.get("classes") in (None, [])

    def test_parse_request_by_classes(self) -> None:
        agent = TeamCommanderAgent()
        message = (
            "Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger, "
            "Spellbreaker, Scrapper pour du WvW zerg."
        )

        req = agent._parse_request(message)  # type: ignore[attr-defined]

        assert req.team_size == 10
        assert req.groups == 2
        classes = req.constraints.get("classes") or []
        # On doit retrouver les 5 classes mentionnées, indépendamment de l'ordre
        expected = {"Firebrand", "Druid", "Harbinger", "Spellbreaker", "Scrapper"}
        assert expected.issubset(set(classes))


class TestTeamCommanderAgentRun:
    """Tests de bout-en-bout sur run()."""

    @pytest.mark.asyncio
    async def test_run_by_roles_builds_two_groups_of_five(self) -> None:
        """Vérifie qu'une requête par rôles produit bien 2x5 slots."""
        agent = TeamCommanderAgent()
        message = (
            "Je veux une équipe de 10 joueurs pour WvW. "
            "Dans chaque groupe il me faut un stabeur, un healer, un booner, "
            "un dps strip et un dps pur."
        )

        result = await agent.run(message)

        assert len(result.groups) == 2
        total_slots = sum(len(g.slots) for g in result.groups)
        assert total_slots == 10
        # Score de synergie cohérent
        assert result.synergy_score in {"S", "A", "B", "C"}
        assert set(result.synergy_details.keys()) >= {
            "stability",
            "healing",
            "boon_share",
            "boon_strip",
            "damage",
            "cleanse",
        }
        assert isinstance(result.notes, list)

    @pytest.mark.asyncio
    async def test_run_by_classes_uses_requested_specs(self) -> None:
        """Vérifie qu'une requête avec classes figées respecte les spés données."""
        agent = TeamCommanderAgent()
        message = (
            "Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger, "
            "Spellbreaker et Scrapper pour du WvW zerg."
        )

        result = await agent.run(message)

        assert len(result.groups) == 2
        total_slots = sum(len(g.slots) for g in result.groups)
        assert total_slots == 10

        # Chaque groupe doit contenir au moins une occurrence de ces 5 spés
        expected_specs = {"Firebrand", "Druid", "Harbinger", "Spellbreaker", "Scrapper"}

        for group in result.groups:
            specs = {slot.specialization for slot in group.slots}
            # On ne force pas l'égalité stricte (l'optimiseur peut varier),
            # mais au minimum toutes les spés demandées doivent être présentes.
            assert expected_specs.issubset(specs)

        # Score de synergie valide
        assert result.synergy_score in {"S", "A", "B", "C"}


@pytest.mark.asyncio
async def test_team_commander_api_collects_team_for_learning(monkeypatch) -> None:
    from app.api import team_commander as tc
    from app.models.learning import DataSource

    class DummyCollector:
        def __init__(self) -> None:
            self.called = False
            self.last_payload = {}

        async def collect_team_from_dict(self, team_data, game_mode, source):
            self.called = True
            self.last_payload = {
                "team_data": team_data,
                "game_mode": game_mode,
                "source": source,
            }

    class DummyPresetService:
        def get_example_armor_for_prefix(self, stats_prefix):
            return []

    class DummyUser:
        def __init__(self, user_id: str) -> None:
            self.id = user_id

    dummy_collector = DummyCollector()
    monkeypatch.setattr(tc, "collector", dummy_collector)
    monkeypatch.setattr(tc, "get_gear_preset_service", lambda: DummyPresetService())

    req = tc.TeamCommandRequest(message="Je veux une équipe de 5 joueurs pour WvW zerg.", experience=None, mode="wvw_zerg")
    user = DummyUser("user-123")

    resp = await tc.command_team(req, current_user=user)

    assert resp["success"] is True
    assert dummy_collector.called is True
    payload = dummy_collector.last_payload
    assert isinstance(payload.get("team_data"), dict)
    assert payload.get("game_mode") == "zerg"
    assert payload.get("source") is DataSource.AI_GENERATED

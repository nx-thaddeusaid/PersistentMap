"""
PersistentMap API contract tests.

Tests the live warServices endpoints for correct response shapes. These tests
are read-only (no POSTs) — safe to run against the production server.

Run against live server:
    pytest tests/

Run against a local server:
    ROGUEWAR_SERVER_URL=http://localhost:8000 pytest tests/
    # or
    pytest tests/ --server-url=http://localhost:8000
"""

import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(session, url, **params):
    resp = session.get(url, params=params or None, timeout=15)
    resp.raise_for_status()
    return resp


def assert_faction_control_list(control_list, system_name):
    assert isinstance(control_list, list), f"{system_name}: controlList must be a list"
    total = 0
    for fc in control_list:
        assert "faction" in fc, f"{system_name}: FactionControl missing 'faction' field"
        assert "percentage" in fc, f"{system_name}: FactionControl missing 'percentage' field"
        pct = fc["percentage"]
        assert isinstance(pct, (int, float)), f"{system_name}: percentage must be numeric, got {type(pct)}"
        assert 0 <= pct <= 100, f"{system_name}: percentage {pct} out of range [0, 100]"
        total += pct
    # Total should be ≤ 100; allow small float drift
    assert total <= 101, f"{system_name}: controlList percentages sum to {total}, expected ≤ 100"


# ---------------------------------------------------------------------------
# StarMap
# ---------------------------------------------------------------------------

class TestStarMap:

    def test_starmap_returns_200(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/StarMap/")
        assert resp.status_code == 200

    def test_starmap_is_json(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/StarMap/")
        data = resp.json()
        assert data is not None

    def test_starmap_has_systems_list(self, session, war_services_url):
        data = get(session, f"{war_services_url}/StarMap/").json()
        assert "systems" in data, "StarMap response missing 'systems' field"
        assert isinstance(data["systems"], list), "'systems' must be a list"

    def test_starmap_systems_nonempty(self, session, war_services_url):
        data = get(session, f"{war_services_url}/StarMap/").json()
        assert len(data["systems"]) > 0, "StarMap has no systems"

    def test_starmap_system_shape(self, session, war_services_url):
        data = get(session, f"{war_services_url}/StarMap/").json()
        # Spot-check the first 10 systems for required fields
        for system in data["systems"][:10]:
            assert "name" in system, f"System missing 'name': {system}"
            assert isinstance(system["name"], str) and system["name"], "system.name must be a non-empty string"
            assert "controlList" in system, f"System '{system['name']}' missing 'controlList'"
            assert_faction_control_list(system["controlList"], system["name"])

    def test_starmap_activeplayers_field(self, session, war_services_url):
        data = get(session, f"{war_services_url}/StarMap/").json()
        for system in data["systems"][:10]:
            assert "activePlayers" in system, f"System '{system.get('name')}' missing 'activePlayers'"
            assert isinstance(system["activePlayers"], int), "activePlayers must be int"
            assert system["activePlayers"] >= 0, "activePlayers must be non-negative"


# ---------------------------------------------------------------------------
# GetSystem
# ---------------------------------------------------------------------------

KNOWN_SYSTEM = "Acrux"  # a system used in existing test suite


class TestGetSystem:

    def test_known_system_returns_200(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/StarMap/System/{KNOWN_SYSTEM}")
        assert resp.status_code == 200

    def test_known_system_has_name(self, session, war_services_url):
        data = get(session, f"{war_services_url}/StarMap/System/{KNOWN_SYSTEM}").json()
        assert data is not None, f"GetSystem({KNOWN_SYSTEM}) returned null"
        assert "name" in data, "System missing 'name'"
        assert data["name"] == KNOWN_SYSTEM

    def test_known_system_control_list(self, session, war_services_url):
        data = get(session, f"{war_services_url}/StarMap/System/{KNOWN_SYSTEM}").json()
        assert "controlList" in data
        assert_faction_control_list(data["controlList"], KNOWN_SYSTEM)

    def test_unknown_system_returns_null(self, session, war_services_url):
        resp = session.get(f"{war_services_url}/StarMap/System/NONEXISTENT_SYSTEM_XYZ", timeout=15)
        # Server returns 200 with null body for unknown systems
        assert resp.status_code == 200
        assert resp.text.strip() in ("null", ""), f"Expected null for unknown system, got: {resp.text[:100]}"


# ---------------------------------------------------------------------------
# GetStartupTime
# ---------------------------------------------------------------------------

class TestStartupTime:

    def test_startup_time_returns_200(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/Info/StartupTime")
        assert resp.status_code == 200

    def test_startup_time_is_nonempty_string(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Info/StartupTime").json()
        assert isinstance(data, str) and data, "StartupTime must be a non-empty string"

    def test_startup_time_is_iso8601(self, session, war_services_url):
        from datetime import datetime
        data = get(session, f"{war_services_url}/Info/StartupTime").json()
        # Server formats with 'o' (ISO 8601 round-trip) — should parse cleanly
        try:
            datetime.fromisoformat(data.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"StartupTime '{data}' is not a valid ISO 8601 timestamp")


# ---------------------------------------------------------------------------
# GetMissionResults
# ---------------------------------------------------------------------------

class TestMissionResults:

    def test_mission_results_returns_200(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/Mission/Results/",
                   MinutesBack="60", MaxResults="10")
        assert resp.status_code == 200

    def test_mission_results_is_list(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Mission/Results/",
                   MinutesBack="60", MaxResults="10").json()
        assert isinstance(data, list), "MissionResults must be a list"

    def test_mission_results_shape(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Mission/Results/",
                   MinutesBack="1440", MaxResults="5").json()
        for result in data:
            assert "winner" in result, f"HistoryResult missing 'winner': {result}"
            assert "loser" in result, f"HistoryResult missing 'loser': {result}"
            assert "system" in result, f"HistoryResult missing 'system': {result}"
            assert "date" in result, f"HistoryResult missing 'date': {result}"
            assert isinstance(result.get("planetSwitched"), bool), "planetSwitched must be bool"

    def test_mission_results_max_results_respected(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Mission/Results/",
                   MinutesBack="525600", MaxResults="3").json()  # 1 year back, max 3
        assert len(data) <= 3, f"MaxResults=3 but got {len(data)} results"


# ---------------------------------------------------------------------------
# GetActivePlayers
# ---------------------------------------------------------------------------

class TestActivePlayers:

    def test_active_players_returns_200(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/Users/Active/", MinutesBack="60")
        assert resp.status_code == 200

    def test_active_players_is_int(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Users/Active/", MinutesBack="60").json()
        assert isinstance(data, int), f"ActivePlayers must be int, got {type(data)}"
        assert data >= 0, "ActivePlayers must be non-negative"


# ---------------------------------------------------------------------------
# GetActiveFactions
# ---------------------------------------------------------------------------

class TestActiveFactions:

    def test_active_factions_returns_200(self, session, war_services_url):
        resp = get(session, f"{war_services_url}/Factions/Active/", MinutesBack="60")
        assert resp.status_code == 200

    def test_active_factions_is_dict(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Factions/Active/", MinutesBack="60").json()
        assert isinstance(data, dict), f"ActiveFactions must be a dict, got {type(data)}"

    def test_active_factions_values_are_ints(self, session, war_services_url):
        data = get(session, f"{war_services_url}/Factions/Active/", MinutesBack="60").json()
        for faction, count in data.items():
            assert isinstance(faction, str) and faction, "faction key must be a non-empty string"
            assert isinstance(count, int) and count >= 0, \
                f"faction '{faction}' count must be non-negative int, got {count}"

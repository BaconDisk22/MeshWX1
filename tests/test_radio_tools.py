"""Regression checks for saved profiles and network discovery."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.web.radio_tools import (
    RadioProfile, ProfileKey, save_profile, list_profiles,
    activate_profile, delete_profile,
)
from app.network_discovery import discover_network_radios


class FakeDB:
    def __init__(self):
        self.settings = {}

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value


@pytest.mark.asyncio
async def test_save_activate_and_delete_profile():
    db = FakeDB()
    tx = SimpleNamespace(reconfigure=AsyncMock(), status=lambda: [])
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db, tx=tx)))
    profile = RadioProfile(name="Base station", protocol="meshtastic", connection="ble", target="ABC")
    saved = await save_profile(request, profile)
    assert len(saved["profiles"]) == 1
    key = ProfileKey(name="Base station", protocol="meshtastic")
    await activate_profile(request, key)
    assert db.settings["meshtastic_conn"] == "ble"
    assert db.settings["meshtastic_host"] == "ABC"
    assert db.settings["meshtastic_enabled"] is True
    tx.reconfigure.assert_awaited_once()
    await delete_profile(request, key)
    assert (await list_profiles(request))["profiles"] == []


@pytest.mark.asyncio
async def test_missing_profile_returns_404():
    db = FakeDB()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))
    with pytest.raises(HTTPException) as err:
        await delete_profile(request, ProfileKey(name="missing", protocol="meshcore"))
    assert err.value.status_code == 404


@pytest.mark.asyncio
async def test_discovery_timeout_validation():
    with pytest.raises(ValueError):
        await discover_network_radios(0)

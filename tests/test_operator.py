"""Safe Phase 4 preview and preference API tests."""
from types import SimpleNamespace
import pytest
from app.web.operator import preview, Preview, preferences, save_preferences, Preferences


class DB:
    def __init__(self):
        self.values = {}

    def get_setting(self, key, default=None):
        return self.values.get(key, default)

    def set_setting(self, key, value):
        self.values[key] = value


@pytest.mark.asyncio
async def test_preview_never_transmits_and_respects_payload_limit():
    result = await preview(Preview(message="🌪" * 1000))
    assert result["transmitted"] is False
    assert result["truncated"] is True
    assert len(result["preview"].encode("utf-8")) <= result["limit"]


@pytest.mark.asyncio
async def test_preferences_round_trip():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=DB())))
    await save_preferences(request, Preferences(compact=True, advanced=True, monitor=False))
    result = await preferences(request)
    assert result == {"compact": True, "advanced": True, "monitor": False}

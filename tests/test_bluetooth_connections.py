"""Regression tests for BLE discovery and transport configuration.

No Bluetooth hardware or radio transmission is needed.
"""
import asyncio
import sys
import types
from unittest.mock import AsyncMock

import pytest

from app.bluetooth_discovery import discover_bluetooth_devices
from app.transmit import _build_transports, MeshtasticTransmitter, MeshCoreTransmitter


class Settings:
    def __init__(self, **values):
        self.values = values

    def get_setting(self, key, default=None):
        return self.values.get(key, default)


def test_ble_targets_are_used_for_both_radios():
    transports = _build_transports(Settings(
        meshtastic_conn="ble", meshtastic_host="MT-ADDRESS",
        meshcore_conn="ble", meshcore_host="MC-ADDRESS",
        meshcore_enabled=True,
    ))
    mt, mc = transports["meshtastic"], transports["meshcore"]
    assert mt.conn == "ble" and mt.target == "MT-ADDRESS"
    assert mc.conn == "ble" and mc.target == "MC-ADDRESS"
    assert isinstance(mt.make(), MeshtasticTransmitter)
    assert isinstance(mc.make(), MeshCoreTransmitter)
    assert mt.make().host == "MT-ADDRESS"
    assert mc.make().host == "MC-ADDRESS"


def test_serial_and_tcp_targets_are_unchanged():
    transports = _build_transports(Settings(
        meshtastic_conn="serial", serial_port="/dev/ttyUSB0",
        meshcore_conn="tcp", meshcore_host="192.168.1.4:4000",
    ))
    assert transports["meshtastic"].target == "/dev/ttyUSB0"
    assert transports["meshcore"].target == "192.168.1.4:4000"


@pytest.mark.asyncio
async def test_bluetooth_discovery_sorts_and_handles_missing_names(monkeypatch):
    scanner = types.ModuleType("bleak")
    scanner.BleakScanner = types.SimpleNamespace(discover=AsyncMock(return_value={
        "b": (types.SimpleNamespace(name=None, address="B"),
              types.SimpleNamespace(local_name="Zulu", rssi=-70)),
        "a": (types.SimpleNamespace(name="Alpha", address="A"),
              types.SimpleNamespace(local_name=None, rssi=-55)),
    }))
    monkeypatch.setitem(sys.modules, "bleak", scanner)
    devices = await discover_bluetooth_devices(2)
    assert [(d.name, d.address, d.rssi) for d in devices] == [
        ("Alpha", "A", -55), ("Zulu", "B", -70)
    ]
    scanner.BleakScanner.discover.assert_awaited_once_with(
        timeout=2, return_adv=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0, -1, 31])
async def test_bluetooth_scan_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        await discover_bluetooth_devices(timeout)

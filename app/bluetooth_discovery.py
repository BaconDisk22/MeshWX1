"""Bluetooth LE discovery for the MeshWX host (Raspberry Pi OS or macOS).

This module deliberately does not connect or transmit. Discovery must execute on
the computer running MeshWX, not on the browser displaying its dashboard.
Install the optional 'bleak' dependency to enable scanning.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class BluetoothDevice:
    name: str
    address: str
    rssi: int | None = None


async def discover_bluetooth_devices(timeout: float = 6.0) -> list[BluetoothDevice]:
    """Return nearby BLE advertisements, sorted by name.

    Addresses on macOS may be CoreBluetooth UUIDs rather than hardware MACs.
    Do not assume every discovered BLE peripheral supports Meshtastic/MeshCore.
    """
    if not 1 <= timeout <= 30:
        raise ValueError("scan timeout must be between 1 and 30 seconds")
    try:
        from bleak import BleakScanner
    except ImportError as exc:
        raise RuntimeError(
            "Bluetooth scanning requires the optional 'bleak' package"
        ) from exc

    # return_adv=True provides RSSI from advertisement data, where available.
    found = await BleakScanner.discover(timeout=timeout, return_adv=True)
    devices = [
        BluetoothDevice(
            name=device.name or advertisement.local_name or "Unknown device",
            address=device.address,
            rssi=advertisement.rssi,
        )
        for device, advertisement in found.values()
    ]
    return sorted(devices, key=lambda d: (d.name.casefold(), d.address))


def scan_bluetooth_devices(timeout: float = 6.0) -> list[BluetoothDevice]:
    """Synchronous helper for CLI diagnostics; not for an active event loop."""
    return asyncio.run(discover_bluetooth_devices(timeout))

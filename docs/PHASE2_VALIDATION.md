# MeshWX Phase 2: Raspberry Pi 4 and Intel Mac validation

These steps are **manual hardware acceptance checks**, not evidence that the
application has already passed hardware testing.

## Raspberry Pi 4 (Raspberry Pi OS)
1. Install Python 3.11+ and Bluetooth/BlueZ support. Ensure Bluetooth is enabled and the running service account can use BlueZ over D-Bus.
2. Install requirements in a virtual environment, then start MeshWX using the existing README instructions.
3. Open Settings → Bluetooth discovery and confirm the radio appears.
4. Save a BLE profile, activate it, and confirm the Radio Tools status changes to connected.
5. Power-cycle the radio; confirm it reconnects after the watchdog interval. Verify no duplicate transmissions.
6. Test USB and network TCP connections independently. Check journal/system logs for Bluetooth permissions errors.

## Intel Mac (macOS Tahoe)
1. Use Python 3.11+ in a virtual environment and install requirements.
2. Grant Bluetooth permission to the terminal or host app in System Settings → Privacy & Security → Bluetooth.
3. Discover a radio; use its CoreBluetooth UUID, not a Linux MAC address.
4. Activate a BLE profile, verify connection, power-cycle and observe reconnect.
5. Verify USB serial permissions and local-network TCP access.

## Release gates
- All automated tests pass on supported Python versions.
- A real Meshtastic BLE device connects, sends a test message, disconnects and reconnects.
- A real MeshCore BLE device does the same.
- USB and TCP transports remain functional.
- No duplicate alert transmission, accidental live-channel test or concurrent reconnect.
- NWS and IPAWS alert paths pass regression tests.
- Test the dark theme on desktop and mobile.
- Check access control before exposing the UI outside a trusted network.

Do not mark hardware checks passed until completed on actual devices.

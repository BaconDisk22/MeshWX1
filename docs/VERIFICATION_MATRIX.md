# WXCOMMAND-PRO — Deployment and Verification Matrix

## Supported workflows under development

| Platform | Install route | Validation required |
| --- | --- | --- |
| Raspberry Pi 4 | Python venv and `deploy/install_pi.sh` | Boot, USB permissions, restart, service recovery, SQLite restore |
| Intel macOS | Python venv and `deploy/build_macos_app.py` | Finder launch, permissions, USB/BLE connectivity, browser opening |
| Linux desktop | Python venv | Startup, network binding, serial access |
| Windows | Existing project packaging | Packaging and executable smoke test before distribution |

## Radio matrix

| Protocol | Connection | Test |
| --- | --- | --- |
| Meshtastic | USB | Connect, disconnect, reconnect, test channel |
| Meshtastic | BLE | Pair, range loss, reconnect, test channel |
| Meshtastic | TCP | Network loss, reconnect, test channel |
| MeshCore | USB | Connect, disconnect, reconnect, test channel |
| MeshCore | BLE/TCP where implemented | Verify adapter support before claiming compatibility |
| Multi-radio | Failover | Primary loss, backup success, no duplicate transmission |

All tests must record OS, Python version, radio firmware, device model, transport, and whether packets were actually received by a separate test node.

## Release safeguards
- Never test by broadcasting fabricated emergency alerts on public channels.
- Keep dry-run on for API/filter tests; use isolated test channels for radio tests.
- Confirm NWS/IPAWS stale, duplicate, cancellation, and geographic behavior.
- Confirm restore of a SQLite backup into a disposable database.
- Keep web management local or behind verified authentication.
- Require passing CI before merging Phase 3 and Phase 4.

## Legacy configuration
WXCOMMAND-PRO recognizes an existing legacy MeshWX database when a new database is not present. Set `MESH_WX_DB` explicitly to override automatic selection. Back up the database before any upgrade.

## Known outstanding work
- True GIS map/radar integration
- Fully installable offline PWA and application icons
- Comprehensive auth/CSRF protection for management routes
- Signed and self-contained installers
- Hardware acceptance tests and verified release binaries

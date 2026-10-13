"""Discover advertised Meshtastic TCP services on the local network.

Discovery is best-effort. A missing mDNS announcement does not imply that a
radio is offline. MeshCore TCP nodes may need a manually entered IP address.
"""
from __future__ import annotations

import asyncio


def _scan(timeout: float) -> list[dict]:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

    found: dict[str, dict] = {}
    zc = Zeroconf()

    class Listener(ServiceListener):
        def add_service(self, zeroconf, service_type, name):
            info = zeroconf.get_service_info(service_type, name, timeout=1000)
            if info:
                for ip in info.parsed_addresses():
                    found[ip] = {"name": name, "host": ip, "port": info.port}

        def update_service(self, zeroconf, service_type, name):
            self.add_service(zeroconf, service_type, name)

        def remove_service(self, zeroconf, service_type, name):
            pass

    try:
        browser = ServiceBrowser(zc, "_meshtastic._tcp.local.", Listener())
        import time
        time.sleep(timeout)
        browser.cancel()
    finally:
        zc.close()
    return sorted(found.values(), key=lambda item: item["host"])


async def discover_network_radios(timeout: float = 5.0) -> list[dict]:
    if not 1 <= timeout <= 20:
        raise ValueError("scan timeout must be between 1 and 20 seconds")
    try:
        import zeroconf
    except ImportError as exc:
        raise RuntimeError("WiFi discovery requires the zeroconf package") from exc
    return await asyncio.to_thread(_scan, timeout)

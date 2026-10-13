"""Read-only Bluetooth discovery UI.

Scanning runs on the MeshWX server host, not in the browser. No pairing,
radio connection, or transmission is performed here.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from html import escape

from ..bluetooth_discovery import discover_bluetooth_devices

router = APIRouter()


@router.get("/settings/bluetooth", response_class=HTMLResponse)
async def bluetooth_page():
    return HTMLResponse("""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MeshWX Bluetooth discovery</title>
<style>
body{font:16px/1.5 system-ui;background:#101820;color:#e5edf2;max-width:780px;margin:3rem auto;padding:0 1rem}
section{background:#233440;border:1px solid #38505b;border-radius:14px;padding:1.5rem}
button{background:#39a6a3;color:#081c20;border:0;padding:.75rem 1.2rem;border-radius:9px;font-weight:700;cursor:pointer}
a{color:#7ed7d2}li{padding:.7rem 0;border-bottom:1px solid #38505b}
</style></head><body><a href="/settings">← Settings</a><h1>Bluetooth device discovery</h1>
<section><p>Scan for nearby Bluetooth LE devices from the computer running MeshWX.
A discovered device is not necessarily a compatible radio. This tool does not connect or transmit.</p>
<button id="scan">Scan nearby devices</button><p id="result" role="status" aria-live="polite"></p></section>
<script>
document.getElementById('scan').addEventListener('click',async()=>{
const b=document.getElementById('scan'),out=document.getElementById('result');
b.disabled=true;out.textContent='Scanning (up to 6 seconds)…';
try{const r=await fetch('/settings/bluetooth/scan',{method:'POST'});
const data=await r.json();if(!r.ok)throw Error(data.detail||'Scan failed');
out.replaceChildren();const p=document.createElement('p');
p.textContent=data.devices.length+' Bluetooth device(s) found';out.append(p);
const ul=document.createElement('ul');
for(const d of data.devices){const li=document.createElement('li');
li.textContent=d.name+' — '+d.address+(d.rssi===null?'':' ('+d.rssi+' dBm)');
ul.append(li)}out.append(ul);
}catch(e){out.textContent='Scan unavailable: '+e.message}
finally{b.disabled=false}
});
</script></body></html>""")


@router.post("/settings/bluetooth/scan")
async def bluetooth_scan():
    from fastapi import HTTPException
    try:
        devices = await discover_bluetooth_devices()
    except (RuntimeError, OSError, TimeoutError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"devices": [
        {"name": d.name, "address": d.address, "rssi": d.rssi}
        for d in devices
    ]}


@router.get("/api/radios/status")
async def radio_status(request: __import__("fastapi").Request):
    """Read-only transport diagnostics for a dashboard or support checks."""
    tx = request.app.state.tx
    return {"radios": tx.status(), "queue_depth": tx.queue_depth,
            "any_connected": tx.connected}

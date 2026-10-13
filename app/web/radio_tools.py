"""Saved radio configurations and a read-only radio tools dashboard.

Profiles are stored in the existing settings database; saving a profile does
not change the active radio configuration or transmit any messages.
"""
from __future__ import annotations

import json
import re
from html import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()
_ALLOWED = ("meshtastic", "meshcore")
_CONN = ("serial", "tcp", "ble")


class RadioProfile(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    protocol: str
    connection: str
    target: str = Field(min_length=1, max_length=255)


def _profiles(db) -> list[dict]:
    raw = db.get_setting("radio_profiles", "[]")
    if isinstance(raw, list):
        return raw
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (TypeError, ValueError):
        return []


@router.get("/api/radios/profiles")
async def list_profiles(request: Request):
    return {"profiles": _profiles(request.app.state.db)}


@router.post("/api/radios/profiles")
async def save_profile(request: Request, profile: RadioProfile):
    if profile.protocol not in _ALLOWED or profile.connection not in _CONN:
        raise HTTPException(status_code=422, detail="Invalid protocol or connection")
    db = request.app.state.db
    profiles = _profiles(db)
    item = profile.model_dump()
    profiles = [p for p in profiles if not (
        p.get("name") == item["name"] and p.get("protocol") == item["protocol"]
    )]
    if len(profiles) >= 20:
        raise HTTPException(status_code=422, detail="Maximum 20 saved profiles")
    profiles.append(item)
    db.set_setting("radio_profiles", json.dumps(profiles))
    return {"profiles": profiles}


@router.get("/settings/radio-tools", response_class=HTMLResponse)
async def radio_tools():
    return HTMLResponse("""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MeshWX radio tools</title><style>
body{font:16px/1.5 system-ui;background:#101a22;color:#e6eff2;max-width:850px;margin:3rem auto;padding:0 1rem}
section{background:#1b2a35;border:1px solid #334753;border-radius:12px;padding:1rem;margin:1rem 0}
button,input,select{padding:.6rem;margin:.3rem;border-radius:6px}
button{background:#67c6be;color:#101a22;cursor:pointer}a{color:#67c6be}
pre{white-space:pre-wrap;overflow-wrap:anywhere}input,select{background:#243944;color:white;border:1px solid #506673}
</style></head><body><a href="/settings">← Settings</a><h1>Radio tools</h1>
<section><h2>Live connection diagnostics</h2><button id="refresh">Refresh status</button><pre id="status" role="status"></pre></section>
<section><h2>Local network discovery</h2><p>Find Meshtastic mDNS announcements on this network. MeshCore may require manual IP configuration.</p>
<button id="discover">Discover network radios</button><pre id="network" role="status"></pre></section>
<section><h2>Saved radio profiles</h2><p>Profiles are stored but never activated automatically. Apply a profile manually in Settings.</p>
<form id="profile"><input name="name" placeholder="Profile name" required maxlength="60">
<select name="protocol"><option>meshtastic</option><option>meshcore</option></select>
<select name="connection"><option>serial</option><option>tcp</option><option>ble</option></select>
<input name="target" placeholder="Port, IP or BLE identifier" required maxlength="255">
<button type="submit">Save profile</button></form><pre id="profiles" role="status"></pre></section>
<script>
const out=(id,value)=>document.getElementById(id).textContent=JSON.stringify(value,null,2);
async function load(id,url,options){try{const r=await fetch(url,options),v=await r.json();out(id,r.ok?v:{error:v.detail||r.status})}catch(e){out(id,{error:String(e)})}}
document.getElementById('refresh').onclick=()=>load('status','/api/radios/status');
document.getElementById('discover').onclick=()=>load('network','/api/radios/discover-network');
document.getElementById('profile').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));await load('profiles','/api/radios/profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(v)})};
load('status','/api/radios/status');load('profiles','/api/radios/profiles');
</script></body></html>""")

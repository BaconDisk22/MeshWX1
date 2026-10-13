"""Saved radio configurations and a read-only radio tools dashboard.

Profiles are stored in the existing settings database; saving a profile does
not change the active radio configuration or transmit any messages.
"""
from __future__ import annotations

import json

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



class ProfileKey(BaseModel):
    name: str
    protocol: str


def _find_profile(db, key: ProfileKey) -> dict:
    match = next((p for p in _profiles(db) if p.get("name") == key.name
                  and p.get("protocol") == key.protocol), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    if match.get("connection") not in _CONN or not match.get("target"):
        raise HTTPException(status_code=422, detail="Profile is invalid")
    return match


@router.delete("/api/radios/profiles")
async def delete_profile(request: Request, key: ProfileKey):
    db = request.app.state.db
    _find_profile(db, key)
    profiles = [p for p in _profiles(db) if not (
        p.get("name") == key.name and p.get("protocol") == key.protocol)]
    db.set_setting("radio_profiles", json.dumps(profiles))
    return {"profiles": profiles}


@router.post("/api/radios/profiles/activate")
async def activate_profile(request: Request, key: ProfileKey):
    """Apply a saved profile and reconnect radios using existing manager logic."""
    db = request.app.state.db
    profile = _find_profile(db, key)
    protocol, conn, target = profile["protocol"], profile["connection"], profile["target"]
    if protocol not in _ALLOWED:
        raise HTTPException(status_code=422, detail="Invalid protocol")
    prefix = "meshtastic" if protocol == "meshtastic" else "meshcore"
    db.set_setting(prefix + "_conn", conn)
    target_key = ("serial_port" if protocol == "meshtastic" else "meshcore_port") if conn == "serial" else prefix + "_host"
    db.set_setting(target_key, target)
    db.set_setting(prefix + "_enabled", True)
    await request.app.state.tx.reconfigure()
    return {"activated": profile, "radios": request.app.state.tx.status()}


@router.post("/api/radios/reconnect")
async def reconnect_radios(request: Request):
    """Manually refresh all configured connections, without sending."""
    await request.app.state.tx.reconfigure()
    return {"radios": request.app.state.tx.status()}


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
<section><h2>Live connection diagnostics</h2><button id="refresh">Refresh status</button><button id="reconnect">Reconnect radios</button><pre id="status" role="status"></pre></section>
<section><h2>Local network discovery</h2><p>Find Meshtastic mDNS announcements on this network. MeshCore may require manual IP configuration.</p>
<button id="discover">Discover network radios</button><pre id="network" role="status"></pre></section>
<section><h2>Saved radio profiles</h2><p>Save configurations, then activate or delete them below. Activation reconnects the selected radio.</p>
<form id="profile"><input name="name" placeholder="Profile name" required maxlength="60">
<select name="protocol"><option>meshtastic</option><option>meshcore</option></select>
<select name="connection"><option>serial</option><option>tcp</option><option>ble</option></select>
<input name="target" placeholder="Port, IP or BLE identifier" required maxlength="255">
<button type="submit">Save profile</button></form><div id="profiles" role="status"></div></section>
<script>
const out=(id,value)=>document.getElementById(id).textContent=JSON.stringify(value,null,2);
async function load(id,url,options){try{const r=await fetch(url,options),v=await r.json();out(id,r.ok?v:{error:v.detail||r.status})}catch(e){out(id,{error:String(e)})}}
async function profiles(){const r=await fetch('/api/radios/profiles'),v=await r.json(),box=document.getElementById('profiles');box.replaceChildren();
for(const p of v.profiles||[]){const row=document.createElement('div');row.style.padding='.6rem';const label=document.createElement('span');label.textContent=p.name+' · '+p.protocol+' · '+p.connection+' · '+p.target;row.append(label);
for(const action of ['Activate','Delete']){const b=document.createElement('button');b.textContent=action;b.type='button';b.onclick=async()=>{if(action==='Delete'&&!confirm('Delete this saved profile?'))return;
const url=action==='Activate'?'/api/radios/profiles/activate':'/api/radios/profiles';
const response=await fetch(url,{method:action==='Activate'?'POST':'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:p.name,protocol:p.protocol})});
if(!response.ok){const v=await response.json();alert(v.detail||'Action failed')}await profiles();await load('status','/api/radios/status')};row.append(b)}box.append(row)}}
document.getElementById('refresh').onclick=()=>load('status','/api/radios/status');
document.getElementById('reconnect').onclick=async()=>{await load('status','/api/radios/reconnect',{method:'POST'});};
document.getElementById('discover').onclick=()=>load('network','/api/radios/discover-network');
document.getElementById('profile').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));await load('status','/api/radios/profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(v)});await profiles()};
load('status','/api/radios/status');profiles();setInterval(()=>load('status','/api/radios/status'),10000);
</script></body></html>""")

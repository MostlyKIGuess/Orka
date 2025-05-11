from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import time

from server.connection_manager import manager
from server.server_config import config

# Set up template directory
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

# Create router
router = APIRouter(tags=["UI"])

@router.get("/dashboard")
async def dashboard(request: Request):
    """Dashboard main page with client list and controls"""
    clients_data = {}
    for cid, cinfo in manager.active_connections.items():
        clients_data[cid] = {
            "name": cinfo.name,
            "platform": cinfo.platform,
            "capabilities": sorted(list(cinfo.capabilities)),
            "connected_since": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(cinfo.registration_time)),
            "last_seen_ago_s": f"{time.monotonic() - cinfo.last_seen_time:.1f}",
            "active_streams": list(cinfo.active_streams.keys()),
            "streams_recording": [sid for sid, s_params in cinfo.active_streams.items() 
                                if s_params.get('is_recording')]
        }
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "clients": clients_data}
    )

@router.get("/clients/{client_id}")
async def client_detail(request: Request, client_id: str):
    client_info = manager.get_client_by_id(client_id)
    if not client_info:
        raise HTTPException(status_code=404, detail="Client not found")

    client = {
        "client_id": client_id,
        "name": client_info.name,
        "platform": client_info.platform,
        "registration_time": time.strftime('%Y-%m-%d %H:%M:%S', 
                                            time.gmtime(client_info.registration_time)),
        "capabilities": sorted(list(client_info.capabilities)),
        "active_streams": client_info.active_streams, # <--- CHANGE HERE
        "streams_recording": [
            sid for sid, p in client_info.active_streams.items() if p.get("is_recording")
        ]
    }

    return templates.TemplateResponse(
        "client_details.html",
        {"request": request, "client": client}
    )
    
@router.get("/client_card_html/{client_id}")
async def client_card_html(request: Request, client_id: str):
    """Generate HTML for a single client card - used for AJAX updates"""
    print(f"Requested client card for ID: {client_id}")
    print(f"Available clients: {list(manager.active_connections.keys())}")
    
    client_info = manager.get_client_by_id(client_id)
    if not client_info:
        print(f"Client not found with ID: {client_id}")
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = {
        "name": client_info.name,
        "platform": client_info.platform,
        "capabilities": sorted(list(client_info.capabilities)),
        "connected_since": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(client_info.registration_time)),
        "last_seen_ago_s": f"{time.monotonic() - client_info.last_seen_time:.1f}",
        "active_streams": list(client_info.active_streams.keys()),
        "streams_recording": [sid for sid, s_params in client_info.active_streams.items() 
                              if s_params.get('is_recording')]
    }
    
    return templates.TemplateResponse(
        "components/client_card.html", 
        {"request": request, "client": client, "client_id": client_id},
        media_type="text/html"
    )
        
    
@router.get("/streams/{stream_id}/status")
async def stream_status(stream_id: str):
    """Get status of a specific stream"""
    found_client = None
    for client in manager.active_connections.values():
        if stream_id in client.active_streams:
            found_client = client
            break
    
    if not found_client:
        raise HTTPException(status_code=404, detail=f"Stream ID '{stream_id}' not found or not active")
    
    stream_info = found_client.active_streams[stream_id]
    
    return {
        "stream_id": stream_id,
        "status": stream_info.get('client_reported_status', 'unknown'),
        "width": stream_info.get('width'),
        "height": stream_info.get('height'),
        "fps": stream_info.get('fps'),
        "is_recording": stream_info.get('is_recording', False)
    }
    
@router.get("/stream/{client_id}/{stream_id}")
async def stream_viewer(request: Request, client_id: str, stream_id: str):
    """Stream viewer page"""
    if client_id not in manager.active_connections:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    
    client = manager.active_connections[client_id]
    
    if stream_id not in client.active_streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")
    
    stream_info = client.active_streams[stream_id]
    
    return templates.TemplateResponse(
        "stream_viewer.html",
        {
            "request": request,
            "client": client,
            "client_id": client_id,
            "stream_id": stream_id,
            "slam_active": stream_info.get("slam_enabled", False),
            "is_recording": stream_info.get("is_recording", False)
        }
    )

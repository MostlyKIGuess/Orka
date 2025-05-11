import asyncio
import base64
import json
import logging
import os
import signal
import sys
import time
import uuid
from typing import Any, Dict, Optional, Union

import cv2
import numpy as np
import uvicorn
from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from server.connection_manager import ClientInfo, manager
from server.server_config import config
from server.stream_manager import stream_manager
from server.ui.routes import router as ui_router
from shared.message_models import (
    ClientRegistration,
    CommandResponse,
    MediaAck,
    PingMessage,
    PongMessage,
    ServerAck,
    StreamStatusUpdate,
    WebSocketMessage,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("server.main")

app = FastAPI(title="Remote Client Control Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# static mounting for UI
static_path = os.path.join(os.path.dirname(__file__), "ui/static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# ui routes
app.include_router(ui_router)

# server state
is_shutting_down = False

# ==================== HELPER FUNCTIONS ====================


async def send_ws_message(
    websocket: WebSocket, message_type: str, payload: Optional[Dict] = None
):
    """Send a standardized WebSocket message"""
    try:
        ws_msg = WebSocketMessage(type=message_type, payload=payload)
        json_data = (
            ws_msg.model_dump(exclude_none=True)
            if hasattr(ws_msg, "model_dump")
            else ws_msg.dict(exclude_none=True)
        )
        await websocket.send_json(json_data)
    except Exception as e:
        logger.error(f"Error sending WebSocket message of type {message_type}: {e}")
        # Log but don't re-raise


# ==================== MESSAGE HANDLERS ====================


async def handle_client_text_message(
    client_info: ClientInfo, msg_type: str, payload: Optional[Union[Dict, BaseModel]]
):
    """Process text messages from clients"""
    logger.debug(f"Client '{client_info.name}': Received text msg type '{msg_type}'")

    payload_dict = (
        payload.model_dump(exclude_none=True)
        if isinstance(payload, BaseModel)
        else payload
    )

    if msg_type == "command_response":
        if isinstance(payload, CommandResponse):
            manager.handle_command_response(
                client_info.client_id,
                payload.command_id,
                payload.status,
                payload.data,
                payload.error_message,
            )
        elif payload_dict:
            try:
                cmd_resp = CommandResponse(**payload_dict)
                manager.handle_command_response(
                    client_info.client_id,
                    cmd_resp.command_id,
                    cmd_resp.status,
                    cmd_resp.data,
                    cmd_resp.error_message,
                )
            except ValidationError as e:
                logger.warning(
                    f"Invalid command_response payload from {client_info.client_id}: {e}"
                )
        else:
            logger.warning(
                f"Missing payload for command_response from {client_info.client_id}"
            )

    elif msg_type == "ping":
        if isinstance(payload, PingMessage):
            pong_model = PongMessage(
                timestamp=payload.timestamp, server_time=time.time()
            )
            await client_info.send_json_message(
                WebSocketMessage(type="pong", payload=pong_model.model_dump())
            )
        else:
            logger.warning(
                f"Invalid or missing payload for ping from {client_info.client_id}"
            )

    elif msg_type == "stream_status":
        if isinstance(payload, StreamStatusUpdate):
            logger.info(
                f"Client '{client_info.name}' status for stream '{payload.stream_id}': {payload.status}. Reason: {payload.reason}"
            )

            if payload.stream_id not in client_info.active_streams:
                client_info.active_streams[payload.stream_id] = {}

            client_info.active_streams[payload.stream_id].update(
                {
                    "client_reported_status": payload.status,
                    "width": payload.width
                    or client_info.active_streams[payload.stream_id].get("width"),
                    "height": payload.height
                    or client_info.active_streams[payload.stream_id].get("height"),
                    "fps": payload.fps
                    or client_info.active_streams[payload.stream_id].get("fps"),
                }
            )

            if payload.status in ["error_on_client", "stopped_by_client"]:
                stream_manager.stop_recording(payload.stream_id)
                client_info.active_streams[payload.stream_id]["is_recording"] = False
        else:
            logger.warning(
                f"Invalid or missing payload for stream_status from {client_info.client_id}"
            )

    else:
        logger.warning(
            f"Client '{client_info.name}': Unhandled text message type '{msg_type}'."
        )


async def handle_client_binary_message(client_info: ClientInfo, binary_data: bytes):
    """Process binary media data from clients"""
    min_len = 4 + 4 + 1  # Prefix + Seq + NullTerm StreamID (empty)
    if len(binary_data) < min_len:
        logger.warning(
            f"Client '{client_info.name}': Short binary message ({len(binary_data)} bytes)."
        )
        return

    try:
        # Parse binary message format
        prefix = binary_data[:4].decode("ascii")
        sequence = int.from_bytes(binary_data[4:8], "big")

        # Find stream_id (null-terminated string)
        stream_id_end_idx = 8
        while (
            stream_id_end_idx < len(binary_data) and binary_data[stream_id_end_idx] != 0
        ):
            stream_id_end_idx += 1

        if stream_id_end_idx >= len(binary_data):
            logger.warning(
                f"Client '{client_info.name}': Malformed binary - no stream_id null terminator."
            )
            return

        stream_id_bytes = binary_data[8:stream_id_end_idx]
        try:
            stream_id = stream_id_bytes.decode("utf-8") if stream_id_bytes else None
        except UnicodeDecodeError:
            logger.error(f"Error decoding stream_id bytes: {stream_id_bytes!r}")
            return
        media_payload = binary_data[stream_id_end_idx + 1 :]

        logger.debug(
            f"Client '{client_info.name}': Binary data. Prefix: {prefix}, Seq: {sequence}, StreamID: '{stream_id}', Size: {len(media_payload)} bytes"
        )

        # Determine media type
        media_type_str = "unknown"
        if prefix == "IMG:":
            media_type_str = "image"
        elif prefix == "VID:":
            media_type_str = "video_frame"

        # Send acknowledgment
        ack_model = MediaAck(
            media_type=media_type_str, sequence=sequence, stream_id=stream_id
        )
        await client_info.send_json_message(
            WebSocketMessage(type="media_ack", payload=ack_model.model_dump())
        )

        # Process media based on type
        if prefix == "IMG:":
            image_format = "jpg"  # TODO: Get actual format from command response
            stream_manager.save_image_data(
                client_info.name, sequence, image_format, media_payload
            )

        elif prefix == "VID:":
            if not stream_id:
                logger.warning(
                    f"Client '{client_info.name}': VID frame without stream_id. Seq: {sequence}. Discarding."
                )
                return

            if stream_id not in client_info.active_streams:
                logger.warning(
                    f"Client '{client_info.name}': Received VID frame for unknown stream '{stream_id}'. Seq: {sequence}"
                )
            else:
                client_info.active_streams[stream_id]["last_frame_seq"] = sequence
                stream_manager.process_video_frame(
                    stream_id, media_payload, client_info
                )

        else:
            logger.warning(
                f"Client '{client_info.name}': Unknown binary prefix '{prefix}'"
            )

    except Exception as e:
        logger.exception(
            f"Client '{client_info.name}': Error processing binary message: {e}"
        )


# ==================== WEBSOCKET ENDPOINT ====================


@app.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    """Main WebSocket connection handler for clients"""
    if is_shutting_down:
        await websocket.close(code=1012, reason="Server is shutting down")
        return

    temp_id = f"pending_{uuid.uuid4().hex[:6]}"
    client_host = (
        getattr(websocket.client, "host", "unknown") if websocket.client else "unknown"
    )
    client_port = (
        getattr(websocket.client, "port", "unknown") if websocket.client else "unknown"
    )
    logger.info(
        "WebSocket connection from %s:%s for '%s'. Temp ID: %s",
        client_host,
        client_port,
        client_name,
        temp_id,
    )

    client_info = None

    try:
        # Accept connection
        await websocket.accept()

        # Wait for registration
        try:
            reg_ws_msg_dict = await asyncio.wait_for(
                websocket.receive_json(), timeout=config.REGISTRATION_TIMEOUT_SECONDS
            )

            # Validate registration message
            reg_ws_msg = WebSocketMessage(**reg_ws_msg_dict)
            if reg_ws_msg.type != "register" or not reg_ws_msg.payload:
                raise ValueError(
                    "First message must be of type 'register' with a payload."
                )

            # Parse registration data
            reg_payload = ClientRegistration(**reg_ws_msg.payload)

        except asyncio.TimeoutError:
            logger.warning(f"{temp_id}: Registration timeout.")
            await send_ws_message(
                websocket, "error", {"message": "Registration timeout"}
            )
            await websocket.close(code=1008, reason="Registration timeout")
            return
        except (ValidationError, ValueError, TypeError) as e:
            logger.warning(f"{temp_id}: Invalid registration message: {e}")
            await send_ws_message(
                websocket, "error", {"message": f"Invalid registration data: {str(e)}"}
            )
            await websocket.close(code=1008, reason="Invalid registration data")
            return

        # Create client and connect
        client_id = str(uuid.uuid4())

        try:
            client_info = await manager.connect(
                websocket,
                client_id,
                reg_payload.client_name,
                reg_payload.platform,
                reg_payload.capabilities,
            )

            # Send welcome message - added error handling here
            try:
                ack_payload = ServerAck(
                    client_id=client_id, message=f"Welcome, {reg_payload.client_name}!"
                )
                await send_ws_message(
                    websocket, "ack_registration", ack_payload.model_dump()
                )
            except Exception as e:
                logger.exception(f"Error sending welcome message: {e}")
                # Continue without disconnecting

        except Exception as e:
            logger.exception(f"Error connecting client {client_name}: {e}")
            await send_ws_message(
                websocket,
                "error",
                {"message": f"Server error during connection: {str(e)}"},
            )
            await websocket.close(code=1011, reason=f"Server error: {type(e).__name__}")
            return

        # Main message processing loop
        while True:
            try:
                data = await websocket.receive()
                # Add null check before accessing attribute
                if client_info:
                    client_info.last_seen_time = time.monotonic()
            except RuntimeError as e:
                if "disconnect message has been received" in str(e):
                    logger.info(
                        f"Client {client_info.client_id if client_info else temp_id} disconnected (disconnect message received)."
                    )
                    break
                else:
                    raise
            client_info.last_seen_time = time.monotonic()

            if "text" in data:
                try:
                    ws_msg = WebSocketMessage(**json.loads(data["text"]))

                    # Parse payload based on message type
                    parsed_payload = None
                    if ws_msg.payload:
                        if ws_msg.type == "command_response":
                            parsed_payload = CommandResponse(**ws_msg.payload)
                        elif ws_msg.type == "ping":
                            parsed_payload = PingMessage(**ws_msg.payload)
                        elif ws_msg.type == "stream_status":
                            parsed_payload = StreamStatusUpdate(**ws_msg.payload)

                    await handle_client_text_message(
                        client_info, ws_msg.type, parsed_payload or ws_msg.payload
                    )

                except json.JSONDecodeError:
                    logger.warning(
                        f"Client {client_info.client_id}: Not a valid JSON message"
                    )
                    await send_ws_message(
                        websocket, "error", {"message": "Invalid JSON format"}
                    )
                except (ValidationError, TypeError, ValueError) as e:
                    logger.warning(
                        f"Client {client_info.client_id}: Invalid message structure: {e}"
                    )
                    await send_ws_message(
                        websocket,
                        "error",
                        {"message": f"Invalid message structure: {str(e)}"},
                    )

            elif "bytes" in data:
                await handle_client_binary_message(client_info, data["bytes"])

    except WebSocketDisconnect as e:
        logger.info(
            f"Client {client_info.client_id if client_info else temp_id} disconnected. Code: {e.code}"
        )
    except Exception as e:
        logger.exception(
            f"Error in WebSocket handler for {client_info.client_id if client_info else temp_id}: {e}"
        )
        if websocket.client_state.CONNECTED:
            try:
                await websocket.close(
                    code=1011, reason=f"Server error: {type(e).__name__}"
                )
            except:
                pass
    finally:
        if client_info:
            # Clean up client connection
            manager.disconnect(client_info.client_id)

            # Stop any active streams
            for stream_id in list(client_info.active_streams.keys()):
                stream_manager.stop_recording(stream_id)

            logger.debug(f"WebSocket handler for {client_info.client_id} finished")


# ==================== HTTP ENDPOINTS ====================


@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Simple HTML status page"""
    return """
    <html>
        <head><title>Remote Client Control Server</title></head>
        <body>
            <h1>Server Running</h1>
            <p>Use the API endpoints to interact with clients.</p>
            <p><a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """


@app.get("/clients")
async def list_clients():
    """List all connected clients and their status"""
    clients_data = {}
    for cid, cinfo in manager.active_connections.items():
        clients_data[cid] = {
            "name": cinfo.name,
            "platform": cinfo.platform,
            "capabilities": sorted(list(cinfo.capabilities)),
            "connected_since": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(cinfo.registration_time)
            ),
            "last_seen_ago_s": f"{time.monotonic() - cinfo.last_seen_time:.1f}",
            "active_streams": list(cinfo.active_streams.keys()),
            "streams_recording": [
                sid
                for sid, s_params in cinfo.active_streams.items()
                if s_params.get("is_recording")
            ],
        }
    return clients_data


@app.post("/clients/{client_id}/commands/{command_action}")
async def send_client_command(
    client_id: str, command_action: str, params: Optional[Dict[str, Any]] = Body(None)
):
    """Send a command to a specific client"""
    if client_id not in manager.active_connections:
        raise HTTPException(status_code=404, detail="Client not found")

    response = await manager.send_command_to_client(client_id, command_action, params)

    if response.get("status") == "error":
        if "Timeout" in response.get("error_message", ""):
            raise HTTPException(status_code=408, detail=response)
        elif "Client not connected" in response.get("error_message", ""):
            raise HTTPException(status_code=404, detail=response)
        else:
            raise HTTPException(status_code=502, detail=response)

    return response


@app.post("/streams/{stream_id}/record/{action}")
async def toggle_stream_recording(stream_id: str, action: str):
    """Start or stop recording for a stream"""
    found_client = None
    for client in manager.active_connections.values():
        if stream_id in client.active_streams:
            found_client = client
            break

    if not found_client:
        raise HTTPException(
            status_code=404, detail=f"Stream ID '{stream_id}' not found or not active"
        )

    stream_params = found_client.active_streams[stream_id]

    if action.lower() == "on":
        stream_params["is_recording"] = True
        return {
            "stream_id": stream_id,
            "recording_status": "enabled",
            "message": "Recording will start with next frame",
        }

    elif action.lower() == "off":
        stream_params["is_recording"] = False
        filepath = stream_manager.stop_recording(stream_id)

        if filepath:
            return {
                "stream_id": stream_id,
                "recording_status": "stopped",
                "file": filepath,
            }
        else:
            return {
                "stream_id": stream_id,
                "recording_status": "disabled",
                "message": "Stream was not recording",
            }

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'on' or 'off'")


@app.post("/api/streams/{stream_id}/slam/{action}")
async def toggle_slam_processing(stream_id: str, action: str):
    """Enable or disable SLAM processing for a stream"""
    found_client = None
    for client in manager.active_connections.values():
        if stream_id in client.active_streams:
            found_client = client
            break

    if not found_client:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": f"Stream ID '{stream_id}' not found or not active",
            },
        )

    stream_params = found_client.active_streams[stream_id]

    if action.lower() == "on":
        stream_params["slam_enabled"] = True
        # Initialize SLAM processor
        stream_manager.initialize_slam(stream_id, found_client.client_id)
        return {"success": True, "slam_enabled": True, "stream_id": stream_id}

    elif action.lower() == "off":
        stream_params["slam_enabled"] = False
        return {"success": True, "slam_enabled": False, "stream_id": stream_id}

    else:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid action. Use 'on' or 'off'"},
        )


@app.get("/api/streams/{stream_id}/slam_view")
async def get_slam_visualization(stream_id: str):
    """Get the SLAM visualization for a stream"""
    import io

    from fastapi.responses import Response

    # Find client with this stream
    client_id = None
    for cid, client in manager.active_connections.items():
        if stream_id in client.active_streams:
            client_id = cid
            break

    if not client_id:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    client = manager.active_connections[client_id]
    stream_params = client.active_streams[stream_id]

    # Check if SLAM is enabled
    if not stream_params.get("slam_enabled", False):
        # Return placeholder image
        placeholder = np.ones((480, 640, 3), dtype=np.uint8) * 100
        cv2.putText(
            placeholder,
            "SLAM not active",
            (50, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )  # type: ignore[attr-defined]

        success, buffer = cv2.imencode(".jpg", placeholder)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to encode placeholder image"
            )

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    # Check if we have a SLAM result
    if "latest_slam_result" not in stream_params:
        placeholder = np.ones((480, 640, 3), dtype=np.uint8) * 100
        cv2.putText(
            placeholder,
            "SLAM processing - please wait",
            (50, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        success, buffer = cv2.imencode(".jpg", placeholder)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to encode placeholder image"
            )

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    # Return the SLAM visualization
    slam_result = stream_params["latest_slam_result"]
    if slam_result and "slam_viz" in slam_result:
        return Response(content=slam_result["slam_viz"], media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="SLAM visualization not available")


@app.get("/api/streams/{stream_id}/slam_map")
async def get_slam_map(stream_id: str):
    """Get the SLAM map for a stream"""
    import io

    from fastapi.responses import Response

    # Find client with this stream
    client_id = None
    for cid, client in manager.active_connections.items():
        if stream_id in client.active_streams:
            client_id = cid
            break

    if not client_id:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    client = manager.active_connections[client_id]
    stream_params = client.active_streams[stream_id]

    # Check if SLAM is enabled
    if not stream_params.get("slam_enabled", False):
        # Return placeholder image
        placeholder = np.ones((400, 400, 3), dtype=np.uint8) * 255
        cv2.putText(
            placeholder,
            "Map not available",
            (50, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2,
        )

        success, buffer = cv2.imencode(".jpg", placeholder)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to encode placeholder image"
            )

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    # Check if we have a SLAM result
    if "latest_slam_result" not in stream_params:
        placeholder = np.ones((400, 400, 3), dtype=np.uint8) * 255
        cv2.putText(
            placeholder,
            "Building map...",
            (50, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2,
        )

        success, buffer = cv2.imencode(".jpg", placeholder)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to encode placeholder image"
            )

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    # Return the SLAM map
    slam_result = stream_params["latest_slam_result"]
    if slam_result and "map" in slam_result:
        return Response(content=slam_result["map"], media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="SLAM map not available")


@app.get("/api/streams/{stream_id}/slam_data")
async def get_slam_data(stream_id: str):
    """Get SLAM data in JSON format"""
    # Find client with this stream
    client_id = None
    for cid, client in manager.active_connections.items():
        if stream_id in client.active_streams:
            client_id = cid
            break

    if not client_id:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    client = manager.active_connections[client_id]
    stream_params = client.active_streams[stream_id]

    # Check if SLAM is enabled
    if not stream_params.get("slam_enabled", False):
        return {"slam_active": False}

    # Return SLAM data
    if "latest_slam_result" in stream_params:
        slam_result = stream_params["latest_slam_result"]
        return {
            "slam_active": True,
            "feature_count": slam_result.get("feature_count", 0),
            "trajectory_length": len(slam_result.get("trajectory", [])),
            "timestamp": slam_result.get("timestamp", 0),
        }
    else:
        return {"slam_active": True, "initializing": True}


# ==================== SHUTDOWN HANDLING ====================


async def cleanup_on_shutdown():
    """Perform graceful shutdown operations"""
    global is_shutting_down
    if is_shutting_down:
        return

    is_shutting_down = True
    logger.info("Server initiating graceful shutdown...")

    # Close all client connections
    active_client_ids = list(manager.active_connections.keys())
    for client_id in active_client_ids:
        client = manager.get_client_by_id(client_id)
        if client and client.websocket:
            try:
                await client.websocket.close(code=1012, reason="Server shutting down")
            except Exception:
                pass
        manager.disconnect(client_id, "Server shutting down")

    # Shutdown stream manager
    stream_manager.shutdown()
    logger.info("Server shutdown complete")


# ==================== SERVER STARTUP ====================

if __name__ == "__main__":
    # Setup signal handlers
    loop = asyncio.get_event_loop()

    # Register signal handlers for graceful shutdown
    signals = (signal.SIGINT, signal.SIGTERM)
    if sys.platform != "win32":
        signals += (signal.SIGHUP,)

    for sig in signals:
        try:
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(cleanup_on_shutdown())
            )
        except (ValueError, NotImplementedError) as e:
            logger.warning(
                f"Could not set signal handler for {getattr(sig, 'name', sig)}: {e}"
            )

    uvicorn_config = uvicorn.Config(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info",
        workers=config.UVICORN_WORKERS,
    )

    server = uvicorn.Server(uvicorn_config)

    try:
        # Run the server with graceful shutdown support
        async def run_server():
            await server.serve()
            await cleanup_on_shutdown()

        loop.run_until_complete(run_server())

    except Exception as e:
        logger.exception(f"Fatal error running server: {e}")

    finally:
        if not is_shutting_down:
            try:
                asyncio.run(cleanup_on_shutdown())
            except RuntimeError as e:
                logger.warning(f"Error during final cleanup: {e}")

        logger.info("Server exited")

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
import uuid

# --- General Purpose Models ---

class Command(BaseModel):
    command_id: str = Field(default_factory=lambda: f"cmd_{uuid.uuid4().hex[:8]}")
    action: str # e.g., "capture_image", "speak_text"
    params: Optional[Dict[str, Any]] = None

class CommandResponse(BaseModel):
    command_id: str
    status: str # "success" or "error"
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ClientRegistration(BaseModel):
    client_name: str
    platform: str
    capabilities: List[str]

class ServerAck(BaseModel):
    client_id: str
    message: str

class PingMessage(BaseModel):
    timestamp: float

class PongMessage(BaseModel):
    timestamp: float # Echoed from Ping ( it's from the client )
    server_time: float # Current server time

class StreamStatusUpdate(BaseModel): # Client -> Server
    stream_id: str
    status: str # "started", "stopped_by_client", "error_on_client"
    reason: Optional[str] = None
    width: Optional[int] = None # When stream starts
    height: Optional[int] = None # When stream starts
    fps: Optional[float] = None # When stream starts

class MediaAck(BaseModel): # Server -> Client
    media_type: str # "image" or "video_frame"
    sequence: int
    stream_id: Optional[str] = None



# Speak Text
class SpeakTextParams(BaseModel):
    text: str
    agent_name: Optional[str] = "Server"

class SpeakTextResponseData(BaseModel):
    message: str = "Text processing initiated."

# Capture Image
class CaptureImageResponseData(BaseModel):
    message: str = "Image capture initiated. Awaiting binary data."
    sequence: int
    format: str # e.g., "jpg", "png"

# Start Video Stream
class StartVideoStreamParams(BaseModel):
    stream_id: Optional[str] = Field(default_factory=lambda: f"stream_{uuid.uuid4().hex[:8]}")
    fps: Optional[int] = 10
    width: Optional[int] = 640
    height: Optional[int] = 480
    quality: Optional[int] = 70 # For JPEG encoding

class StartVideoStreamResponseData(BaseModel):
    stream_id: str
    message: str = "Video stream initiated by client."

# Stop Video Stream
class StopVideoStreamParams(BaseModel):
    stream_id: str

class StopVideoStreamResponseData(BaseModel):
    stream_id: str
    message: str = "Video stream stopped by client."


# Union of all possible WebSocket message payloads for the server to receive from client
ClientMessagePayload = Union[
    ClientRegistration,
    CommandResponse, # Client responding to a server command
    PingMessage,     # Client pinging server
    StreamStatusUpdate # Client updating server about its stream
]

# Union of all possible WebSocket message payloads for the client to receive from server
ServerMessagePayload = Union[
    ServerAck,
    Command,        # Server sending command to client
    PongMessage,    # Server responding to client ping
    MediaAck        # Server acknowledging receipt of binary media
]

# Message wrapper for JSON WebSocket communication
# All text messages will be of this type
class WebSocketMessage(BaseModel):
    type: str # e.g., "registration", "command", "command_response", "ping", "ack_registration"
    payload: Optional[Dict[str, Any]] = None # Will be parsed into specific Pydantic models above

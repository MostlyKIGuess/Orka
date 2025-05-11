import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from shared.message_models import WebSocketMessage  # Use shared models

logger = logging.getLogger("server.connection_manager")


class ClientInfo:
    def __init__(
        self,
        client_id: str,
        websocket: WebSocket,
        name: str,
        platform: str,
        capabilities: List[str],
    ):
        self.client_id: str = client_id
        self.websocket: WebSocket = websocket
        self.name: str = name
        self.platform: str = platform
        self.capabilities: Set[str] = set(capabilities)
        self.registration_time: float = time.monotonic()
        self.last_seen_time: float = time.monotonic()
        self.active_streams: Dict[str, Dict[str, Any]] = (
            {}
        )  # stream_id -> {is_recording, fps, width, height, etc.}
        # For commands sent TO this client that server is awaiting response for
        self.pending_commands: Dict[str, asyncio.Future] = {}  # command_id -> Future

    async def send_json_message(self, message: WebSocketMessage):
        try:
            if self.websocket.client_state == self.websocket.client_state.CONNECTED:
                await self.websocket.send_json(
                    message.model_dump(exclude_none=True)
                )  # Pydantic v2
                # For Pydantic v1: await self.websocket.send_json(message.dict(exclude_none=True))
                logger.debug(f"Sent to {self.client_id} ({self.name}): {message.type}")
            else:
                logger.warning(
                    f"Attempted to send to disconnected client {self.client_id} ({self.name})"
                )
        except Exception as e:
            logger.error(
                f"Error sending message to {self.client_id} ({self.name}): {e}"
            )

    async def send_binary_data(self, data: bytes):
        try:
            if self.websocket.client_state == self.websocket.client_state.CONNECTED:
                await self.websocket.send_bytes(data)
                logger.debug(
                    f"Sent binary data to {self.client_id} ({self.name}), size: {len(data)}"
                )
            else:
                logger.warning(
                    f"Attempted to send binary data to disconnected client {self.client_id} ({self.name})"
                )
        except Exception as e:
            logger.error(
                f"Error sending binary data to {self.client_id} ({self.name}): {e}"
            )


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, ClientInfo] = {}  # client_id -> ClientInfo
        self.client_id_by_websocket: Dict[WebSocket, str] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        name: str,
        platform: str,
        capabilities: List[str],
    ) -> ClientInfo:
        """Add a new client connection"""
        # Create client info
        client_info = ClientInfo(
            client_id=client_id,
            websocket=websocket,
            name=name,
            platform=platform,
            capabilities=capabilities,
        )

        # Store the connection in both dictionaries
        self.active_connections[client_id] = client_info
        self.client_id_by_websocket[websocket] = client_id  # Add this line

        logger.info(
            f"Client connected: {client_id} ({name}). Platform: {platform}. Capabilities: {capabilities}"
        )
        return client_info

    def disconnect(self, client_id: str, reason: str = "Client disconnected"):
        client_info = self.active_connections.pop(client_id, None)
        if client_info:
            self.client_id_by_websocket.pop(client_info.websocket, None)
            # Cancel any pending commands for this client
            for cmd_id, future in list(client_info.pending_commands.items()):
                if not future.done():
                    future.set_exception(
                        RuntimeError(
                            f"Client disconnected before command {cmd_id} response: {reason}"
                        )
                    )
                client_info.pending_commands.pop(cmd_id, None)
            logger.info(
                f"Client '{client_info.name}' ({client_id}) disconnected. Reason: {reason}"
            )
        else:
            logger.debug(
                f"Attempted to disconnect client {client_id}, but not found in active connections."
            )

    def get_client_by_websocket(self, websocket: WebSocket) -> Optional[ClientInfo]:
        client_id = self.client_id_by_websocket.get(websocket)
        if client_id:
            return self.active_connections.get(client_id)
        return None

    def get_client_by_id(self, client_id: str) -> Optional[ClientInfo]:
        return self.active_connections.get(client_id)

    async def broadcast(self, message: WebSocketMessage):  # Example broadcast
        for client_id, client_info in self.active_connections.items():
            await client_info.send_json_message(message)

    async def send_command_to_client(
        self,
        client_id: str,
        command_action: str,
        params: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Dict:
        client_info = self.get_client_by_id(client_id)
        if not client_info:
            return {
                "status": "error",
                "error_message": f"Client {client_id} not connected.",
            }

        from server.server_config import (
            config as server_config,
        )  # Avoid circular import at top level

        # Create command using Pydantic model
        from shared.message_models import Command

        cmd_obj = Command(action=command_action, params=params)

        # Wrap it in WebSocketMessage
        ws_message = WebSocketMessage(
            type="command", payload=cmd_obj.model_dump()
        )  # Pydantic v2
        # For Pydantic v1: ws_message = WebSocketMessage(type="command", payload=cmd_obj.dict())

        future = asyncio.Future()
        client_info.pending_commands[cmd_obj.command_id] = future

        await client_info.send_json_message(ws_message)
        logger.info(
            f"Sent command '{command_action}' (ID: {cmd_obj.command_id}) to client {client_info.name} ({client_id})"
        )

        try:
            actual_timeout = (
                timeout
                if timeout is not None
                else server_config.DEFAULT_COMMAND_TIMEOUT_SECONDS
            )
            # The future will be resolved by handle_command_response when client sends it back
            response_data = await asyncio.wait_for(future, timeout=actual_timeout)
            return response_data  # This should be the dict: {"status": ..., "data": ..., "error_message": ...}
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for response to command '{command_action}' ({cmd_obj.command_id}) from {client_id}"
            )
            return {
                "status": "error",
                "command_id": cmd_obj.command_id,
                "error_message": "Timeout waiting for client response.",
            }
        except Exception as e:
            logger.error(
                f"Error during command {cmd_obj.command_id} processing for {client_id}: {e}"
            )
            return {
                "status": "error",
                "command_id": cmd_obj.command_id,
                "error_message": f"Server error: {str(e)}",
            }
        finally:
            client_info.pending_commands.pop(cmd_obj.command_id, None)

    def handle_command_response(
        self,
        client_id: str,
        command_id: str,
        status: str,
        data: Optional[Dict],
        error_message: Optional[str],
    ):
        client_info = self.get_client_by_id(client_id)
        if not client_info:
            logger.warning(f"Received command response for unknown client {client_id}")
            return

        future = client_info.pending_commands.get(command_id)
        if not future:
            logger.warning(
                f"Received response for unknown or timed-out command_id '{command_id}' from {client_id}."
            )
            return

        if future.done():
            logger.warning(
                f"Future for command '{command_id}' already done. Ignoring new response."
            )
            return

        response_package = {
            "status": status,
            "command_id": command_id,
            "data": None,
            "error_message": None,
        }
        if data:
            response_package["data"] = data
        if error_message:
            response_package["error_message"] = error_message

        future.set_result(response_package)
        logger.info(
            f"Processed command response for {command_id} from {client_id}: Status {status}"
        )


# Global instance of ConnectionManager
manager = ConnectionManager()

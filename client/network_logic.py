import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

import cv2
import websockets

from client.client_config import ORIGINAL_HANDLERS_AVAILABLE, ClientConfig

# Import original handlers if available for direct use
if ORIGINAL_HANDLERS_AVAILABLE:
    from src.audio_handler import speak as original_speak_func
    from src.image_handler import (
        _capture_image_linux,
        _capture_image_rpi,
        _capture_image_termux,
    )
else:
    original_speak_func = None
    _capture_image_termux, _capture_image_rpi, _capture_image_linux = None, None, None


# Import shared message models
# Assuming 'shared' is in project_root, and project_root is in sys.path
from shared.message_models import (
    ClientRegistration,
    Command,
    CommandResponse,
    MediaAck,
    PingMessage,
    PongMessage,
    ServerAck,
    StreamStatusUpdate,
    WebSocketMessage,
)

logger = logging.getLogger("client.network_logic")


class NetworkLogic:
    def __init__(
        self, config: ClientConfig, shutdown_callback: Optional[Callable] = None
    ):
        self.config = config
        self.websocket: Optional[Any] = None
        self.client_id: Optional[str] = None  # Assigned by server
        self.is_running: bool = False
        self.reconnect_attempts: int = 0
        self.shutdown_callback = shutdown_callback  # To signal main to exit

        self._ping_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._active_video_streams: Dict[str, asyncio.Task] = {}  # stream_id -> Task
        self._media_sequence_counter: int = 0
        self._pending_outgoing_commands: Dict[str, asyncio.Future] = {}

    async def connect_and_run(self, startup_only: bool = False):
        self.is_running = True
        while self.is_running:
            try:
                logger.info(
                    f"Attempting to connect to server: {self.config.SERVER_URL} (startup_only={startup_only})"
                )
                # Create URL with client name, handling None case
                base_url = self.config.SERVER_URL or ""
                connection_url = base_url + f"/{self.config.CLIENT_NAME}"

                async with websockets.connect(
                    connection_url,
                    open_timeout=self.config.WEBSOCKET_TIMEOUT_SECONDS,
                    close_timeout=self.config.WEBSOCKET_TIMEOUT_SECONDS,
                    ping_interval=None,  # We handle pings manually
                ) as ws:
                    self.websocket = ws
                    self.reconnect_attempts = 0  # Reset on successful connection
                    logger.info("WebSocket connection established.")

                    if not await self._perform_registration():
                        # Registration failed, server likely closed connection or will soon
                        await self._handle_disconnect("Registration failed.")
                        continue  # Trigger reconnect logic

                        # if only startup (handshake), bail out now
                    if startup_only:
                        logger.info(
                            "Startup-only mode: registration complete, returning."
                        )
                        return

                    # Start background tasks for this connection
                    self._ping_task = asyncio.create_task(self._ping_loop())
                    self._receive_task = asyncio.create_task(self._receive_loop())

                    # Keep connection alive by awaiting these tasks
                    # If either task exits (e.g., due to connection error), it will trigger disconnect
                    done, pending = await asyncio.wait(
                        [self._ping_task, self._receive_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in pending:
                        task.cancel()  # Cancel other task if one completed/failed

                    # Check if any task raised an exception (usually indicates connection issue)
                    for task in done:
                        if task.exception():
                            logger.error(
                                f"Awaiting background task resulted in error: {task.exception()}"
                            )
                            # This will lead to disconnect in finally block

            except (
                websockets.exceptions.InvalidURI,
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError,
                websockets.exceptions.WebSocketException,
            ) as e:
                logger.error(f"Connection failed: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error in connect_and_run main loop: {e}")
            finally:
                # This block executes after connection loss or if inner tasks complete
                await self._handle_disconnect(
                    "Connection lost or task ended."
                )  # Clean up current connection state
                if (
                    self.is_running
                ):  # If we are supposed to be running, attempt reconnect
                    self.reconnect_attempts += 1
                    if self.reconnect_attempts > self.config.MAX_RECONNECT_ATTEMPTS:
                        logger.error(
                            "Max reconnection attempts reached. Stopping client."
                        )
                        self.is_running = False
                        if self.shutdown_callback:
                            await self.shutdown_callback()  # Signal main to exit
                        break  # Exit while loop

                    delay = self.config.RECONNECT_DELAY_SECONDS * (
                        2 ** min(self.reconnect_attempts - 1, 4)
                    )  # Exponential backoff up to a limit
                    logger.info(
                        f"Reconnecting in {delay} seconds (attempt {self.reconnect_attempts})..."
                    )
                    await asyncio.sleep(delay)
                else:  # Not self.is_running, so we are shutting down
                    logger.info("Client is stopping, no reconnection attempt.")
                    break
        logger.info("NetworkLogic run loop finished.")

    async def _perform_registration(self) -> bool:
        if not self.websocket:
            return False

        reg_payload = ClientRegistration(
            client_name=self.config.CLIENT_NAME,
            platform=self.config.PLATFORM,
            capabilities=self.config.CAPABILITIES,
        )
        reg_msg = WebSocketMessage(
            type="register", payload=reg_payload.model_dump()
        )  # Pydantic v2
        # For Pydantic v1: reg_msg = WebSocketMessage(type="register", payload=reg_payload.dict())

        try:
            await self.websocket.send(
                reg_msg.model_dump_json(exclude_none=True)
            )  # Pydantic v2
            # For Pydantic v1: await self.websocket.send(reg_msg.json(exclude_none=True))

            response_str = await asyncio.wait_for(
                self.websocket.recv(), timeout=self.config.WEBSOCKET_TIMEOUT_SECONDS
            )
            response_dict = json.loads(response_str)
            ack_msg = WebSocketMessage(**response_dict)

            if ack_msg.type == "ack_registration" and ack_msg.payload:
                ack_payload = ServerAck(**ack_msg.payload)
                self.client_id = ack_payload.client_id
                logger.info(
                    f"Successfully registered with server. Client ID: {self.client_id}. Message: {ack_payload.message}"
                )
                return True
            elif ack_msg.type == "error" and ack_msg.payload:
                logger.error(
                    f"Registration failed by server: {ack_msg.payload.get('message')}"
                )
                return False
            else:
                logger.error(f"Unexpected registration response: {ack_msg}")
                return False
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for registration acknowledgement.")
            return False
        except (
            websockets.exceptions.ConnectionClosed,
            json.JSONDecodeError,
            TypeError,
            KeyError,
        ) as e:
            logger.error(f"Error during registration communication: {e}")
            return False

    async def _ping_loop(self):
        try:
            # Replace websocket.open with a proper connection check
            while self.websocket and getattr(self.websocket, "open", True):
                await asyncio.sleep(self.config.PING_INTERVAL_SECONDS)
                ping_model = PingMessage(timestamp=time.time())
                ping_msg = WebSocketMessage(
                    type="ping", payload=ping_model.model_dump()
                )
                await self.send_json_message(ping_msg)
                logger.debug("Sent ping to server.")
        except asyncio.CancelledError:
            logger.info("Ping loop cancelled.")
        except Exception as e:
            logger.exception(f"Error in ping loop: {e}")

    async def _receive_loop(self):
        try:
            async for message_str in self.websocket:  # type: ignore
                try:
                    data_dict = json.loads(message_str)
                    ws_msg = WebSocketMessage(**data_dict)  # Validate overall structure

                    # Parse payload based on type for stricter validation if needed
                    parsed_payload = None
                    if ws_msg.payload:
                        if ws_msg.type == "command":
                            parsed_payload = Command(**ws_msg.payload)
                        elif ws_msg.type == "pong":
                            parsed_payload = PongMessage(**ws_msg.payload)
                        elif ws_msg.type == "media_ack":
                            parsed_payload = MediaAck(**ws_msg.payload)
                        elif (
                            ws_msg.type == "command_response"
                        ):  # Response to a client-initiated command
                            parsed_payload = CommandResponse(**ws_msg.payload)
                        # Add other specific server-to-client types

                    await self._handle_server_message(
                        ws_msg.type, parsed_payload or ws_msg.payload
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                    KeyError,
                    Exception,
                ) as e:  # Incl Pydantic ValidationError
                    logger.error(
                        f"Error processing message from server: {e}. Raw: {message_str[:200]}"
                    )
        except asyncio.CancelledError:
            logger.info("Receive loop cancelled.")
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(
                f"Connection closed by server (or network issue). Code: {e.code}, Reason: {e.reason}"
            )
        except Exception as e:
            logger.exception(f"Critical error in receive loop: {e}")
        # When this loop exits, it signals connect_and_run to handle disconnect/reconnect

    async def _handle_server_message(
        self, msg_type: str, payload: Optional[Dict | Any]
    ):  # Payload can be Pydantic model
        # If payload is a Pydantic model, convert to dict for some handlers if they expect dict
        payload_dict = payload
        if payload is not None and hasattr(payload, "model_dump"):
            model_dump_fn = getattr(payload, "model_dump")
            payload_dict = model_dump_fn(exclude_none=True)
        # For Pydantic v1: payload_dict = payload.dict(exclude_none=True) if hasattr(payload, 'dict') else payload

        logger.debug(
            f"Received server message type '{msg_type}'. Payload: {payload_dict}"
        )

        if msg_type == "command":
            if isinstance(payload, Command):  # Use the validated Pydantic model
                await self._execute_command(payload)
            elif payload_dict:  # Fallback if not parsed as Pydantic model yet
                try:
                    cmd_model = Command(**payload_dict)
                    await self._execute_command(cmd_model)
                except Exception as e:  # Pydantic ValidationError
                    logger.error(
                        f"Invalid command payload: {e}. Payload: {payload_dict}"
                    )
            else:
                logger.error("Command message received without payload.")

        elif msg_type == "pong":
            if isinstance(payload, PongMessage):
                latency = time.time() - payload.timestamp
                logger.debug(
                    f"Received pong. Latency: {latency:.3f}s. Server time: {payload.server_time}"
                )
            else:
                logger.warning(f"Malformed pong received: {payload_dict}")

        elif msg_type == "media_ack":
            if isinstance(payload, MediaAck):
                logger.info(
                    f"Server ACK for {payload.media_type}: seq={payload.sequence}, stream_id='{payload.stream_id}'"
                )
            else:
                logger.warning(f"Malformed media_ack received: {payload_dict}")

        elif msg_type == "command_response":
            if isinstance(payload, CommandResponse):
                future = self._pending_outgoing_commands.get(payload.command_id)
                if future and not future.done():
                    future.set_result(payload.model_dump(exclude_none=True))
                elif future and future.done():
                    logger.warning(
                        f"Received command_response for already completed command {payload.command_id}"
                    )
                else:
                    logger.warning(
                        f"Received command_response for unknown command_id {payload.command_id}. Might be a response to a server-initiated command if not tracked here, or a late response."
                    )
            elif (
                payload_dict and "command_id" in payload_dict
            ):  # Fallback if not parsed as Pydantic
                future = self._pending_outgoing_commands.get(payload_dict["command_id"])
                if future and not future.done():
                    future.set_result(payload_dict)
                # Similar logging for unknown/late responses can be added here
            else:
                logger.warning(f"Malformed command_response received: {payload_dict}")
        else:
            logger.warning(f"Unhandled message type from server: {msg_type}")

    async def _execute_command(self, cmd: Command):
        action_handler = getattr(self, f"_action_{cmd.action}", None)
        if action_handler and callable(action_handler):
            # Ensure the handler is an async function before awaiting
            if asyncio.iscoroutinefunction(action_handler):
                try:
                    await action_handler(cmd.command_id, cmd.params or {})
                except Exception as e:
                    logger.exception(
                        f"Error executing action '{cmd.action}' for command {cmd.command_id}: {e}"
                    )
                    await self.send_command_response(
                        cmd.command_id,
                        "error",
                        error_message=f"Client execution error: {str(e)}",
                    )
            else:
                logger.error(
                    f"Action handler for '{cmd.action}' is not an awaitable coroutine function."
                )
                await self.send_command_response(
                    cmd.command_id,
                    "error",
                    error_message=f"Client internal error: Action '{cmd.action}' is not correctly implemented as async.",
                )
        else:
            logger.warning(f"Unknown command action: {cmd.action}")
            await self.send_command_response(
                cmd.command_id, "error", error_message=f"Unknown action: {cmd.action}"
            )

    async def send_command(
        self,
        action: str,
        params: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Dict:
        """Sends a command to the server and waits for a response."""
        if not self.websocket or not getattr(self.websocket, "open", True):
            return {
                "status": "error",
                "error_message": "WebSocket not connected.",
            }

        cmd_to_send = Command(action=action, params=params or {})
        ws_msg = WebSocketMessage(
            type="command", payload=cmd_to_send.model_dump(exclude_none=True)
        )

        future = asyncio.Future()
        self._pending_outgoing_commands[cmd_to_send.command_id] = future

        await self.send_json_message(ws_msg)
        logger.debug(
            f"Sent command '{action}' (ID: {cmd_to_send.command_id}) to server."
        )

        try:
            # Use a default timeout from config if not provided
            actual_timeout = (
                timeout
                if timeout is not None
                else self.config.WEBSOCKET_TIMEOUT_SECONDS
            )  # Or a new config like DEFAULT_REQUEST_TIMEOUT
            response_data = await asyncio.wait_for(future, timeout=actual_timeout)
            return response_data
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for response to command '{action}' (ID: {cmd_to_send.command_id}) from server."
            )
            return {
                "status": "error",
                "command_id": cmd_to_send.command_id,
                "error_message": "Timeout waiting for server response.",
            }
        except Exception as e:
            logger.error(
                f"Error during client command {cmd_to_send.command_id} processing: {e}"
            )
            return {
                "status": "error",
                "command_id": cmd_to_send.command_id,
                "error_message": f"Client-side error: {str(e)}",
            }
        finally:
            self._pending_outgoing_commands.pop(cmd_to_send.command_id, None)

    async def send_json_message(self, ws_msg: WebSocketMessage):
        if self.websocket and getattr(self.websocket, "open", True):
            try:
                await self.websocket.send(
                    ws_msg.model_dump_json(exclude_none=True)
                )  # Pydantic v2
                # For Pydantic v1: await self.websocket.send(ws_msg.json(exclude_none=True))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(
                    f"Failed to send JSON (type {ws_msg.type}): Connection closed."
                )
            except Exception as e:
                logger.error(f"Error sending JSON (type {ws_msg.type}): {e}")
        else:
            logger.warning(
                f"Cannot send JSON (type {ws_msg.type}): WebSocket not open."
            )

    async def send_binary_message(
        self, prefix: bytes, sequence: int, stream_id_str: Optional[str], data: bytes
    ):
        if self.websocket and getattr(self.websocket, "open", True):
            try:
                header = prefix
                header += sequence.to_bytes(4, "big")
                header += (
                    stream_id_str.encode("utf-8") if stream_id_str else b""
                ) + b"\x00"  # Null terminated stream_id
                message = header + data
                await self.websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                logger.warning(
                    f"Failed to send binary data (prefix {prefix.decode()}): Connection closed."
                )
            except Exception as e:
                logger.error(
                    f"Error sending binary data (prefix {prefix.decode()}): {e}"
                )
        else:
            logger.warning(
                f"Cannot send binary data (prefix {prefix.decode()}): WebSocket not open."
            )

    async def send_command_response(
        self,
        command_id: str,
        status: str,
        data: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ):
        resp_payload = CommandResponse(
            command_id=command_id, status=status, data=data, error_message=error_message
        )
        ws_msg = WebSocketMessage(
            type="command_response", payload=resp_payload.model_dump(exclude_none=True)
        )  # Pydantic v2
        # For Pydantic v1: ws_msg = WebSocketMessage(type="command_response", payload=resp_payload.dict(exclude_none=True))
        await self.send_json_message(ws_msg)

    async def send_stream_status_update(
        self,
        stream_id: str,
        status: str,
        reason: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
    ):
        status_payload = StreamStatusUpdate(
            stream_id=stream_id,
            status=status,
            reason=reason,
            width=width,
            height=height,
            fps=fps,
        )
        ws_msg = WebSocketMessage(
            type="stream_status", payload=status_payload.model_dump(exclude_none=True)
        )  # Pydantic v2
        # For Pydantic v1: ws_msg = WebSocketMessage(type="stream_status", payload=status_payload.dict(exclude_none=True))
        await self.send_json_message(ws_msg)

    async def stop(self, reason: str = "Client stopping."):
        logger.info(f"NetworkLogic stopping. Reason: {reason}")
        self.is_running = False  # Signal loops to stop

        # Stop active video streams first
        for stream_id, task in list(self._active_video_streams.items()):
            logger.info(
                f"Stopping video stream task for {stream_id} due to client stop."
            )
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(
                    f"Error awaiting video stream task {stream_id} during stop: {e}"
                )
        self._active_video_streams.clear()

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self.websocket and getattr(self.websocket, "open", True):
            try:
                await self.websocket.close(reason=reason)
                logger.info("WebSocket connection closed by client.")
            except Exception as e:
                logger.error(f"Error closing WebSocket during stop: {e}")
        self.websocket = None

    async def _handle_disconnect(self, reason: str):
        logger.warning(f"Handling disconnect. Reason: {reason}")
        # Stop all active stream tasks associated with this connection
        for stream_id, task in list(self._active_video_streams.items()):
            logger.info(f"Stopping video stream task {stream_id} due to disconnect.")
            task.cancel()
            # Don't await here to avoid blocking disconnect logic if stream task hangs
            # asyncio.create_task(self._await_stream_task_on_disconnect(task, stream_id))
        self._active_video_streams.clear()

        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        self.websocket = None  # Clear websocket object
        self.client_id = None  # Clear client ID
        # Reconnect logic is handled in connect_and_run's finally block

    # --- Action Handlers (Called by _execute_command) ---

    async def _action_capture_image(self, command_id: str, _params: Dict):
        if not ORIGINAL_HANDLERS_AVAILABLE or not self.config.ORIGINAL_APP_CONFIG:
            await self.send_command_response(
                command_id,
                "error",
                error_message="Image handler or app config not available on client.",
            )
            return

        logger.info("Executing capture_image action...")
        image_path = None
        capture_func = None

        # Select appropriate capture function based on platform
        if self.config.PLATFORM == "termux" and _capture_image_termux:
            capture_func = _capture_image_termux
        elif self.config.PLATFORM == "rpi" and _capture_image_rpi:
            capture_func = _capture_image_rpi
        elif (
            self.config.PLATFORM in ["linux", "windows", "macos"]
            and _capture_image_linux
        ):
            capture_func = _capture_image_linux

        if not capture_func:
            await self.send_command_response(
                command_id,
                "error",
                error_message=f"No image capture method for platform {self.config.PLATFORM}.",
            )
            return

        try:
            # These internal capture methods usually take output_path from original_app_config
            loop = asyncio.get_running_loop()
            # Run the synchronous capture function in an executor
            image_path = await loop.run_in_executor(
                None, capture_func, self.config.ORIGINAL_APP_CONFIG.TEMP_IMAGE_PATH
            )

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    image_data = f.read()

                img_format = (
                    os.path.splitext(image_path)[1].lstrip(".").lower() or "jpg"
                )
                self._media_sequence_counter += 1
                sequence = self._media_sequence_counter

                # 1. Send JSON response first
                await self.send_command_response(
                    command_id,
                    "success",
                    data={
                        "message": "Image captured. Sending binary data.",
                        "sequence": sequence,
                        "format": img_format,
                    },
                )
                # 2. Then send binary data
                await self.send_binary_message(b"IMG:", sequence, None, image_data)

                # Optional: Clean up temp image
                if image_path == self.config.ORIGINAL_APP_CONFIG.TEMP_IMAGE_PATH:
                    try:
                        os.remove(image_path)
                    except OSError as e:
                        logger.warning(f"Could not remove temp image {image_path}: {e}")
            else:
                await self.send_command_response(
                    command_id,
                    "error",
                    error_message="Failed to capture image or image path invalid.",
                )
        except Exception as e:
            logger.exception(f"Error during _action_capture_image: {e}")
            await self.send_command_response(
                command_id, "error", error_message=f"Client error: {str(e)}"
            )

    async def _action_speak_text(self, command_id: str, params: Dict):
        if not ORIGINAL_HANDLERS_AVAILABLE or not original_speak_func:
            await self.send_command_response(
                command_id,
                "error",
                error_message="Audio speak handler not available on client.",
            )
            return

        text_to_speak = params.get("text")
        agent_name = params.get("agent_name", "Server")
        if not text_to_speak:
            await self.send_command_response(
                command_id, "error", error_message="No text provided."
            )
            return

        logger.info(f"Executing speak_text action: '{text_to_speak}' as {agent_name}")
        try:
            loop = asyncio.get_running_loop()
            # original_speak_func might be blocking (e.g., pyttsx3.runAndWait())
            await loop.run_in_executor(
                None, original_speak_func, text_to_speak, agent_name
            )
            await self.send_command_response(
                command_id,
                "success",
                data={"message": "Text spoken (or fallback printed)."},
            )
        except Exception as e:
            logger.exception(f"Error during _action_speak_text: {e}")
            await self.send_command_response(
                command_id, "error", error_message=f"Client error: {str(e)}"
            )

    async def _action_start_video_stream(self, command_id: str, params: Dict):
        if "stream_video" not in self.config.CAPABILITIES:
            await self.send_command_response(
                command_id,
                "error",
                error_message="Video streaming not supported/configured on client.",
            )
            return

        # Use Pydantic model for params validation if available, or dict access
        from shared.message_models import StartVideoStreamParams  # Local import ok here

        try:
            stream_params = StartVideoStreamParams(**params)
        except Exception as e:  # Pydantic ValidationError
            logger.error(f"Invalid start_video_stream params: {e}. Params: {params}")
            await self.send_command_response(
                command_id, "error", error_message=f"Invalid stream parameters: {e}"
            )
            return

        stream_id = (
            stream_params.stream_id
        )  # This will have a default factory value if not provided
        if stream_id is None or stream_id == "":
            logger.error(
                f"Invalid stream_id provided: {stream_id}. Must be a non-empty string."
            )
            await self.send_command_response(
                command_id,
                "error",
                error_message="Invalid stream_id provided. Must be a non-empty string.",
            )
            return

        if stream_id in self._active_video_streams:
            await self.send_command_response(
                command_id, "error", error_message=f"Stream {stream_id} already active."
            )
            return

        logger.info(
            f"Starting video stream task for {stream_id} with params: {stream_params}"
        )
        try:
            # Create and store the streaming task
            video_task = asyncio.create_task(
                self._video_stream_loop(
                    stream_id,
                    stream_params.fps or self.config.DEFAULT_STREAM_FPS,
                    stream_params.quality or self.config.DEFAULT_STREAM_QUALITY,
                    stream_params.width or self.config.DEFAULT_STREAM_WIDTH,
                    stream_params.height or self.config.DEFAULT_STREAM_HEIGHT,
                )
            )
            self._active_video_streams[stream_id] = video_task
            # Send success response to server
            await self.send_command_response(
                command_id,
                "success",
                data={"stream_id": stream_id, "message": "Video stream initiated."},
            )
            # Client also sends a stream_status update when it actually starts sending frames
            # This is handled within _video_stream_loop after camera opens
        except Exception as e:
            logger.exception(f"Failed to start video stream task for {stream_id}: {e}")
            if stream_id in self._active_video_streams:
                del self._active_video_streams[stream_id]  # Clean up
            await self.send_command_response(
                command_id,
                "error",
                error_message=f"Client error starting stream: {str(e)}",
            )

    async def _action_stop_video_stream(self, command_id: str, params: Dict):
        from shared.message_models import StopVideoStreamParams  # Local import ok here
        
        logger.info(f"STOP STREAM COMMAND RECEIVED: command_id={command_id}, params={params}")
        
        try:
            stop_params = StopVideoStreamParams(**params)
        except Exception as e:  # Pydantic ValidationError
            logger.error(f"Invalid stop_video_stream parameters: {e}")
            await self.send_command_response(
                command_id,
                "error",
                error_message=f"Invalid stop_video_stream parameters: {e}",
            )
            return
    
        stream_id = stop_params.stream_id
        logger.info(f"Attempting to stop video stream {stream_id} as per server command.")
        
        # Log current active streams for debugging
        logger.info(f"Current active streams: {list(self._active_video_streams.keys())}")
        
        if stream_id in self._active_video_streams:
            task = self._active_video_streams.pop(stream_id)
            logger.info(f"Found stream task {stream_id}, cancelling it now")
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5.0)  # Give task time to clean up
                logger.info(f"Stream task {stream_id} cleanup completed successfully")
            except asyncio.CancelledError:
                logger.info(f"Video stream task {stream_id} cancelled successfully.")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for video stream task {stream_id} to finish after cancel.")
            except Exception as e:
                logger.error(f"Error during supervised stop of video stream {stream_id}: {e}")
    
            # Send status update first to ensure server knows stream is stopping
            await self.send_stream_status_update(
                stream_id, 
                "stopped_by_client", 
                reason="Stream stopped by server command"
            )
            
            # Then send command response
            await self.send_command_response(
                command_id,
                "success",
                data={
                    "stream_id": stream_id,
                    "message": "Video stream stopped successfully",
                },
            )
            logger.info(f"Stream {stream_id} stop complete - command response sent")
        else:
            logger.warning(f"Stream {stream_id} not found in active streams: {list(self._active_video_streams.keys())}")
            await self.send_command_response(
                command_id,
                "error",
                error_message=f"Stream {stream_id} not found or not active.",
            )

    async def _video_stream_loop(
        self, stream_id: str, fps: int, quality: int, width: int, height: int
    ):
        cap = None
        is_this_stream_active_flag = True  # Local to this task
        try:
            logger.info(
                f"Stream {stream_id}: Initializing camera ({width}x{height} @ {fps}fps Q{quality})..."
            )

            if self.config.PLATFORM == "termux":
                logger.error(
                    f"Stream {stream_id}: OpenCV VideoCapture is unlikely to work well in Termux without root/special setup. This stream will likely fail."
                )

            cap = cv2.VideoCapture(0)  # Use default camera index
            if not cap.isOpened():
                logger.error(f"Stream {stream_id}: Cannot open camera.")
                if self.websocket and getattr(self.websocket, "open", True):
                    await self.send_stream_status_update(
                        stream_id, "error_on_client", reason="Cannot open camera."
                    )
                else:
                    logger.warning(
                        f"Stream {stream_id}: WebSocket closed, cannot send 'cannot open camera' status."
                    )
                return

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            if actual_fps == 0:  # Some cameras return 0, use requested fps
                actual_fps = fps
            logger.info(
                f"Stream {stream_id}: Camera opened. Actual FPS from cam: {actual_fps if actual_fps > 0 else 'N/A'}. Aiming for ~{fps} FPS."
            )

            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if self.websocket and getattr(self.websocket, "open", True):
                await self.send_stream_status_update(
                    stream_id,
                    "started",
                    width=actual_width,
                    height=actual_height,
                    fps=fps,
                )
            else:
                logger.warning(
                    f"Stream {stream_id}: WebSocket closed, cannot send 'started' status."
                )
                is_this_stream_active_flag = (
                    False  # If we can't send started, stop the loop
                )

            frame_interval = 1.0 / fps

            while is_this_stream_active_flag and self.is_running:
                if not self.is_running:
                    logger.info(
                        f"Stream {stream_id}: Client is not running. Stopping video loop."
                    )
                    is_this_stream_active_flag = False
                    break
                if stream_id not in self._active_video_streams:
                    logger.info(
                        f"Stream {stream_id}: Stream ID no longer in active_video_streams. Stopping video loop."
                    )
                    is_this_stream_active_flag = False
                    break
                if not (self.websocket and getattr(self.websocket, "open", True)):
                    logger.warning(
                        f"Stream {stream_id}: WebSocket is closed or unavailable. Stopping video loop."
                    )
                    is_this_stream_active_flag = False
                    break

                loop_start_time = time.monotonic()

                ret, frame = cap.read()
                if not ret:
                    logger.error(
                        f"Stream {stream_id}: Failed to capture frame from camera."
                    )
                    await asyncio.sleep(0.1)  # Avoid busy loop if camera fails
                    continue

                # Resize if camera output doesn't match requested/actual dimensions
                if frame.shape[1] != actual_width or frame.shape[0] != actual_height:
                    frame = cv2.resize(frame, (actual_width, actual_height))

                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                result, encoded_frame_bytes = cv2.imencode(
                    ".jpg",
                    frame,
                    tuple(
                        encode_param
                    ),  # Use tuple(encode_param) if error, but list should be fine
                )

                if not result:
                    logger.warning(f"Stream {stream_id}: Failed to JPEG encode frame.")
                    continue

                self._media_sequence_counter += 1
                await self.send_binary_message(
                    b"VID:",
                    self._media_sequence_counter,
                    stream_id,
                    encoded_frame_bytes.tobytes(),
                )

                elapsed_time = time.monotonic() - loop_start_time
                sleep_duration = frame_interval - elapsed_time
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)

        except asyncio.CancelledError:
            logger.info(f"Video stream loop {stream_id} was cancelled.")
            is_this_stream_active_flag = False
        except Exception as e:
            logger.exception(f"Error in video stream loop {stream_id}: {e}")
            if (
                is_this_stream_active_flag
            ):  # Only send error if not already stopped/cancelled
                if self.websocket and getattr(self.websocket, "open", True):
                    await self.send_stream_status_update(
                        stream_id, "error_on_client", reason=f"Runtime error: {str(e)}"
                    )
                else:
                    logger.warning(
                        f"Stream {stream_id}: WebSocket closed, cannot send error_on_client status update for: {str(e)}"
                    )
            is_this_stream_active_flag = False
        finally:
            if cap:
                cap.release()
                logger.info(f"Stream {stream_id}: Camera released.")

            # Remove from active streams regardless of how the loop ended
            self._active_video_streams.pop(stream_id, None)

            # If the loop was explicitly cancelled or stopped due to client/websocket issues,
            # is_this_stream_active_flag should be False.
            # Sending a "stopped_by_client" status here might be redundant if the server
            # already knows (e.g., from a stop_video_stream command or client disconnect).
            # However, if the loop terminated for an unexpected reason while still "active",
            # this provides a final status.
            if is_this_stream_active_flag:
                logger.warning(
                    f"Stream {stream_id}: Loop ended with is_this_stream_active_flag still true. This is unexpected."
                )
                if self.websocket and getattr(self.websocket, "open", True):
                    await self.send_stream_status_update(
                        stream_id,
                        "stopped_by_client",
                        reason="Stream loop ended unexpectedly on client.",
                    )
            else:
                # If not active, it means it was cancelled, errored, or stopped by a check.
                # The server should be informed by other means (e.g. _action_stop_video_stream, disconnect, or error status already sent)
                logger.info(
                    f"Stream {stream_id}: Loop ended, is_this_stream_active_flag is False. No final status sent from here."
                )

            logger.info(f"Video stream loop {stream_id} finished cleanup.")

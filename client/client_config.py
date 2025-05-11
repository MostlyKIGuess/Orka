import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional

try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # This assumes 'config.py' from the original app is in the project root
    import config as original_app_config  # from project root

    CLIENT_PLATFORM = original_app_config.PLATFORM

    original_src_path = os.path.join(project_root, "src")
    if original_src_path not in sys.path:
        sys.path.insert(0, original_src_path)

    from src.audio_handler import listen as original_listen
    from src.audio_handler import speak as original_speak
    from src.image_handler import _capture_image_linux  # Internal methods
    from src.image_handler import _capture_image_rpi, _capture_image_termux

    ORIGINAL_HANDLERS_AVAILABLE = True
except ImportError as e:
    logging.error(
        f"CRITICAL: Could not import original app_config or handlers: {e}. Client capabilities will be severely limited."
    )
    CLIENT_PLATFORM = "unknown"  # Fallback
    if "TERMUX_VERSION" in os.environ:
        CLIENT_PLATFORM = "termux"
    elif sys.platform.startswith("linux"):
        CLIENT_PLATFORM = "linux"
    elif sys.platform.startswith("win"):
        CLIENT_PLATFORM = "windows"
    elif sys.platform.startswith("darwin"):
        CLIENT_PLATFORM = "macos"

    original_speak, original_listen = None, None
    ORIGINAL_HANDLERS_AVAILABLE = False
    logging.info(f"Falling back to detected platform: {CLIENT_PLATFORM}")


@dataclass
class ClientConfig:
    """Configuration for the network client (FastAPI server version)."""

    SERVER_URL: Optional[str] = os.getenv(
        "REMOTE_SERVER_URL", "ws://localhost:8765"
    )  # Default to common FastAPI port

    CLIENT_NAME: str = field(
        default_factory=lambda: f"{CLIENT_PLATFORM.capitalize()}Client-{os.uname().nodename if hasattr(os, 'uname') else 'Host'}"
    )
    PLATFORM: str = CLIENT_PLATFORM
    CAPABILITIES: List[str] = field(default_factory=list)

    # Original App Specifics
    ORIGINAL_APP_CONFIG: Optional[Any] = original_app_config
    ORIGINAL_APP_SRC_PATH: str = (
        os.path.join(project_root, "src") if "project_root" in locals() else ""
    )

    # Video streaming settings
    DEFAULT_STREAM_FPS: int = 10
    DEFAULT_STREAM_QUALITY: int = 70
    DEFAULT_STREAM_WIDTH: int = 640
    DEFAULT_STREAM_HEIGHT: int = 480

    # Network settings
    PING_INTERVAL_SECONDS: int = 20
    RECONNECT_DELAY_SECONDS: int = 5
    MAX_RECONNECT_ATTEMPTS: int = 5
    WEBSOCKET_TIMEOUT_SECONDS: int = 10  # For send/recv operations

    def __post_init__(self):
        if not self.CAPABILITIES:  # Only set defaults if not provided
            # Base capability for all clients
            # self.CAPABILITIES.append("text_input") # Not directly a server command

            if ORIGINAL_HANDLERS_AVAILABLE:
                if original_speak:
                    self.CAPABILITIES.append("speak_text")
                # if original_listen: # For STT, if server ever commands it
                #     self.CAPABILITIES.append("listen_audio")

                # Check specific image capture methods
                can_capture_image = False
                if self.PLATFORM == "termux" and _capture_image_termux:
                    can_capture_image = True
                elif self.PLATFORM == "rpi" and _capture_image_rpi:
                    can_capture_image = True
                elif self.PLATFORM == "linux" and _capture_image_linux:
                    can_capture_image = True
                # Could add windows/macos here if _capture_image_linux is generic opencv based

                if can_capture_image:
                    self.CAPABILITIES.append("capture_image")

            try:
                import cv2  # noqa

                self.CAPABILITIES.append("stream_video")
            except ImportError:
                logging.info(
                    "OpenCV (cv2) not found. Video streaming capability disabled for client."
                )

            self.CAPABILITIES = sorted(list(set(self.CAPABILITIES)))

        logging.info(
            f"Client Config Initialized: Name='{self.CLIENT_NAME}', Platform='{self.PLATFORM}', Server='{self.SERVER_URL}'"
        )
        logging.info(f"Capabilities: {self.CAPABILITIES}")
        if not ORIGINAL_HANDLERS_AVAILABLE:
            logging.warning(
                "Original application handlers not loaded. Client actions will be stubs or fail."
            )


# Global instance (optional, main_client can create it)
# client_config_instance = ClientConfig()

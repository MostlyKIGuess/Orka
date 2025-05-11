import logging
import os
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SERVER_PORT", 8765))

    BASE_OUTPUT_DIR: str = "output_data"
    IMAGE_OUTPUT_DIR: str = field(init=False)
    VIDEO_STREAM_RECORDINGS_DIR: str = field(init=False)

    CLIENT_TIMEOUT_SECONDS: int = 60
    REGISTRATION_TIMEOUT_SECONDS: int = 15
    DEFAULT_COMMAND_TIMEOUT_SECONDS: float = 30.0

    STREAM_VIEWER_FPS: float = 15.0
    STREAM_VIEWER_CODEC: str = "mp4v"
    STREAM_VIEWER_VIDEO_EXTENSION: str = ".mp4"

    # Uvicorn specific if needed, though usually passed via CLI
    # keep this 1 because uvicorn will spawn multiple processes, and then there was an error around there benig an issue with permissions on camera and stuff
    UVICORN_WORKERS = 1

    def __post_init__(self):
        os.makedirs(self.BASE_OUTPUT_DIR, exist_ok=True)
        self.IMAGE_OUTPUT_DIR = os.path.join(self.BASE_OUTPUT_DIR, "images")
        self.VIDEO_STREAM_RECORDINGS_DIR = os.path.join(
            self.BASE_OUTPUT_DIR, "video_recordings"
        )
        os.makedirs(self.IMAGE_OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.VIDEO_STREAM_RECORDINGS_DIR, exist_ok=True)

        logger = logging.getLogger("server.config")
        logger.info(f"Server output directories (FastAPI version):")
        logger.info(f"  Images: {os.path.abspath(self.IMAGE_OUTPUT_DIR)}")
        logger.info(
            f"  Video Recordings: {os.path.abspath(self.VIDEO_STREAM_RECORDINGS_DIR)}"
        )


config = ServerConfig()

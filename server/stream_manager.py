import cv2
import numpy as np
import logging
import os
import time
from typing import Dict, Optional, Tuple, Any
from server.server_config import config as server_config # Use the global config
from .slam_processor import SLAMProcessor

logger = logging.getLogger("server.stream_manager")

class StreamManager:
    def __init__(self):
        self.recordings_dir = server_config.VIDEO_STREAM_RECORDINGS_DIR
        self.default_fps = server_config.STREAM_VIEWER_FPS
        self.default_codec = server_config.STREAM_VIEWER_CODEC
        self.video_extension = server_config.STREAM_VIEWER_VIDEO_EXTENSION
        
        self._recorders: Dict[str, Tuple[cv2.VideoWriter, str]] = {} # stream_id -> (recorder, filepath)
        self.slam_processors = {}  # To store SLAM processors by stream_id
        # If you wanted to re-implement live viewing via server (e.g., separate process or thread using OpenCV):
        # self._live_view_queues: Dict[str, queue.Queue] = {}
        # self._viewer_threads: Dict[str, threading.Thread] = {}
        self._is_shutting_down = False
        logger.info(f"StreamManager initialized. Recordings to: {os.path.abspath(self.recordings_dir)}")

    def start_recording(self, stream_id: str, frame_width: int, frame_height: int, client_name: Optional[str] = None, fps: Optional[float] = None) -> bool:
        if self._is_shutting_down: return False
        if stream_id in self._recorders:
            logger.warning(f"Stream {stream_id} already recording.")
            return True

        actual_fps = fps if fps is not None and fps > 0 else self.default_fps
        client_part = f"_{client_name.replace(' ', '_')}" if client_name else ""
        filename = f"{stream_id}{client_part}_{int(time.time())}{self.video_extension}"
        filepath = os.path.join(self.recordings_dir, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*self.default_codec)
        try:
            recorder = cv2.VideoWriter(filepath, fourcc, actual_fps, (frame_width, frame_height))
            if not recorder.isOpened():
                logger.error(f"Failed to open VideoWriter for {stream_id} at {filepath}.")
                return False
            self._recorders[stream_id] = (recorder, filepath)
            logger.info(f"Recording started for stream {stream_id} to {filepath} ({frame_width}x{frame_height} @ {actual_fps:.1f} FPS)")
            return True
        except Exception as e:
            logger.exception(f"Error creating VideoWriter for {stream_id}: {e}")
            return False

    def stop_recording(self, stream_id: str) -> Optional[str]:
        if stream_id not in self._recorders: return None
        recorder_tuple = self._recorders.pop(stream_id, None)
        if recorder_tuple:
            recorder, filepath = recorder_tuple
            try:
                recorder.release()
                logger.info(f"Recording stopped for {stream_id}. File: {filepath}")
                return filepath
            except Exception as e:
                logger.exception(f"Error releasing VideoWriter for {stream_id}: {e}")
        return None

    def process_video_frame(self, stream_id: str, frame_data: bytes, client_info_ref: Any):
        if self._is_shutting_down: return
    
        try:
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                logger.error(f"Stream {stream_id}: Failed to decode video frame.")
                return
        except Exception as e:
            logger.exception(f"Stream {stream_id}: Error decoding video frame: {e}")
            return
    
        stream_params = client_info_ref.active_streams.get(stream_id, {})
        
        # Process with SLAM if enabled for this stream
        if stream_params.get('slam_enabled', False):
            if stream_id not in self.slam_processors:
                self.initialize_slam(stream_id, client_info_ref.name)
            
            if stream_id in self.slam_processors:
                try:
                    # Process frame through SLAM and get visualization
                    slam_result = self.slam_processors[stream_id].process_frame(frame)
                    # Store the most recent SLAM result for UI access
                    stream_params['latest_slam_result'] = slam_result
                except Exception as e:
                    logger.exception(f"Error processing SLAM for stream {stream_id}: {e}")
        
        # Handle recording (existing code)
        if stream_params.get('is_recording', False):
            if stream_id not in self._recorders:
                height, width = frame.shape[:2]
                fps = stream_params.get('fps', self.default_fps)
                self.start_recording(stream_id, width, height, client_info_ref.name, fps)
            
            if stream_id in self._recorders:
                recorder, _ = self._recorders[stream_id]
                try:
                    recorder.write(frame)
                except Exception as e:
                    logger.exception(f"Error writing frame to recorder for {stream_id}: {e}")
                    self.stop_recording(stream_id)
                    stream_params['is_recording'] = False

    def save_image_data(self, client_name: str, sequence: int, image_format: str, image_data: bytes) -> Optional[str]:
        if self._is_shutting_down: return None
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"img_{client_name.replace(' ', '_')}_{timestamp}_seq{sequence}.{image_format.lower()}"
            filepath = os.path.join(server_config.IMAGE_OUTPUT_DIR, filename) # Use config directly

            with open(filepath, "wb") as f:
                f.write(image_data)
            logger.info(f"Saved image from {client_name}, seq {sequence}, to: {filepath} ({len(image_data)} bytes)")
            return filepath
        except Exception as e:
            logger.exception(f"Error saving image data from {client_name}, seq {sequence}: {e}")
            return None

    def shutdown(self):
        logger.info("Shutting down StreamManager...")
        self._is_shutting_down = True
        for stream_id in list(self._recorders.keys()):
            self.stop_recording(stream_id)
        self._recorders.clear()
        logger.info("StreamManager shutdown complete.")
    def initialize_slam(self, stream_id, client_id):
        """Initialize SLAM processing for a stream."""
        if stream_id not in self.slam_processors:
            self.slam_processors[stream_id] = SLAMProcessor(client_id, stream_id)
            return True
        return False

# Global instance
stream_manager = StreamManager()

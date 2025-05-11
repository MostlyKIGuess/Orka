import cv2
import numpy as np
import logging
import threading

logger = logging.getLogger("server.slam_processor")

class SLAMProcessor:
    def __init__(self, client_id, stream_id):
        """Initialize the SLAM processor"""
        self.client_id = client_id
        self.stream_id = stream_id
        self.map = None  # Will store the 2D map representation
        self.trajectory = []  # Will store the client's movement path
        self.feature_points = []  # Will store detected feature points
        self.is_initialized = False
        self.lock = threading.Lock()  # For thread safety
        
        # Initialize the ORB feature detector
        self.orb = cv2.ORB_create(nfeatures=1000)
        # Initialize the feature matcher
        self.matcher = cv2.BFMatcher_create(cv2.NORM_HAMMING, crossCheck=True)
        
        # Store previous frame data
        self.prev_frame = None
        self.prev_kp = None
        self.prev_des = None
        
        logger.info(f"SLAM processor initialized for client {client_id}, stream {stream_id}")
    
    def process_frame(self, frame):
        """Process a video frame for SLAM"""
        with self.lock:
            # Convert to grayscale for feature detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect features
            kp, des = self.orb.detectAndCompute(gray, None)
            
            # Create visualization frame
            slam_viz = frame.copy()
            
            # Draw detected feature points
            cv2.drawKeypoints(slam_viz, kp, slam_viz, color=(0, 255, 0), flags=0)
            
            # If we have previous frame data, calculate movement
            if self.prev_frame is not None and self.prev_kp is not None and self.prev_des is not None and des is not None:
                # Match features
                try:
                    matches = self.matcher.match(self.prev_des, des)
                    # Sort by distance
                    matches = sorted(matches, key=lambda x: x.distance)
                    
                    # Use top matches for movement estimation
                    good_matches = matches[:30] if len(matches) > 30 else matches
                    
                    if len(good_matches) >= 8:  # Need at least 8 points for homography
                        # Extract matched keypoints
                        prev_pts = np.array([self.prev_kp[m.queryIdx].pt for m in good_matches], dtype=np.float32)
                        curr_pts = np.array([kp[m.trainIdx].pt for m in good_matches], dtype=np.float32)
                        
                        # Calculate homography
                        H, mask = cv2.findHomography(prev_pts, curr_pts, cv2.RANSAC, 5.0)
                        
                        if H is not None:
                            # Extract movement (translation) from homography
                            tx = H[0, 2]
                            ty = H[1, 2]
                            
                            # Update trajectory
                            if not self.trajectory:
                                self.trajectory.append((int(frame.shape[1]/2), int(frame.shape[0]/2)))
                            else:
                                last_x, last_y = self.trajectory[-1]
                                new_x = int(last_x + tx)
                                new_y = int(last_y + ty)
                                self.trajectory.append((new_x, new_y))
                            
                            # Draw trajectory on map view
                            map_size = (400, 400)
                            if self.map is None:
                                self.map = np.ones((map_size[0], map_size[1], 3), dtype=np.uint8) * 255
                            
                            # Draw trajectory line
                            if len(self.trajectory) > 1:
                                # Scale and center the trajectory for the map view
                                map_center = (map_size[0]//2, map_size[1]//2)
                                scaled_traj = []
                                for x, y in self.trajectory:
                                    # Scale trajectory to fit in map
                                    sx = int(map_center[0] + (x - frame.shape[1]/2) * 0.5)
                                    sy = int(map_center[1] + (y - frame.shape[0]/2) * 0.5)
                                    scaled_traj.append((sx, sy))
                                
                                # Draw the trajectory lines
                                for i in range(1, len(scaled_traj)):
                                    cv2.line(self.map, scaled_traj[i-1], scaled_traj[i], (0, 0, 255), 2)
                                
                                # Draw current position
                                cv2.circle(self.map, scaled_traj[-1], 5, (255, 0, 0), -1)
                    
                    # Draw matches on visualization frame
                    match_viz = cv2.drawMatches(
                        self.prev_frame, self.prev_kp, 
                        frame, kp, 
                        good_matches, None, 
                        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
                    )
                    
                    # Resize match visualization to match frame size
                    if match_viz.shape[1] > slam_viz.shape[1]:
                        match_viz = cv2.resize(match_viz, (slam_viz.shape[1], int(match_viz.shape[0] * slam_viz.shape[1] / match_viz.shape[1])))
                
                except Exception as e:
                    logger.error(f"Error matching features: {e}")
                    match_viz = None
            else:
                match_viz = None
            
            # Update previous frame data
            self.prev_frame = gray.copy()
            self.prev_kp = kp
            self.prev_des = des
            
            self.is_initialized = True
            
            # Prepare result dict with visualizations
            result = {
                'slam_viz': self._encode_frame(slam_viz),
                'map': self._encode_frame(self.map) if self.map is not None else None,
                'matches': self._encode_frame(match_viz) if match_viz is not None else None,
                'trajectory': self.trajectory.copy(),
                'timestamp': cv2.getTickCount() / cv2.getTickFrequency()
            }
            
            return result
    
    def _encode_frame(self, frame):
        """Encode a frame to JPEG for web display"""
        success, encoded_img = cv2.imencode('.jpg', frame)
        if success:
            return encoded_img.tobytes()
        return None

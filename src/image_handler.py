import logging
import os
import subprocess
import config  

# Uncomment the one you need for RPi
# import cv2 # For OpenCV with USB Webcam
# from picamera2 import Picamera2, Preview # For RPi Camera Module v3 (adjust for older versions)
# import time # Usually needed with camera libraries


def _capture_image_termux(output_path=config.TEMP_IMAGE_PATH):
    """Captures an image using Termux:API."""
    logging.info("Attempting image capture via Termux:API...")
    try:
        # Command to take a photo with the back camera (usually '0')
        # You might need to experiment with camera IDs (e.g., '1' for front)
        command = ["termux-camera-photo", "-c", "0", output_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(f"Termux camera command output: {result.stdout}")
        if os.path.exists(output_path):
            logging.info(f"Image saved successfully to {output_path}")
            return output_path
        else:
            logging.error("Termux command ran but image file was not created.")
            return None
    except FileNotFoundError:
        logging.error(
            "`termux-camera-photo` command not found. Is Termux:API installed and configured?"
        )
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Termux camera command failed with error code {e.returncode}:")
        logging.error(f"Stderr: {e.stderr}")
        logging.error(f"Stdout: {e.stdout}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during Termux image capture: {e}")
        return None


def _capture_image_rpi(output_path=config.TEMP_IMAGE_PATH):
    """Captures an image using Raspberry Pi camera (Picamera or OpenCV)."""
    logging.info("Attempting image capture via RPi camera...")

    # Using Picamera2 (Recommended for RPi Camera Modules) 
    # Make sure to install it: pip install picamera2
    # try:
    #     picam2 = Picamera2()
    #     # Optional: Configure resolution, etc.
    #     camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
    #     picam2.configure(camera_config)
    #     # Optional: Start preview if connected to a display
    #     # picam2.start_preview(Preview.QTGL) # Or Preview.DRM
    #     picam2.start()
    #     time.sleep(2) # Allow camera to adjust focus and exposure
    #     picam2.capture_file(output_path)
    #     picam2.stop()
    #     # picam2.stop_preview() # If preview was started
    #     picam2.close()
    #     logging.info(f"Image saved successfully via Picamera2 to {output_path}")
    #     return output_path
    # except ImportError:
    #     logging.warning("Picamera2 library not found. Cannot use RPi Camera Module.")
    #     return None
    # except Exception as e:
    #     logging.error(f"Failed to capture image with Picamera2: {e}")
    #     # Clean up if Picamera2 object exists
    #     try:
    #         if 'picam2' in locals() and picam2.is_open:
    #             picam2.stop()
    #             picam2.close()
    #     except Exception as cleanup_e:
    #         logging.error(f"Error during picamera cleanup: {cleanup_e}")
    #     return None

    # Using OpenCV (Good for USB Webcams) 
    # Make sure to install it: pip install opencv-python
    # try:
    #     # Use 0 for the default camera, may need to change if multiple cameras
    #     cap = cv2.VideoCapture(0)
    #     if not cap.isOpened():
    #         logging.error("Cannot open camera via OpenCV.")
    #         return None
    #     time.sleep(1) # Give camera time to initialize
    #     ret, frame = cap.read()
    #     if not ret:
    #         logging.error("Can't receive frame (stream end?). Exiting.")
    #         cap.release()
    #         return None
    #     cv2.imwrite(output_path, frame)
    #     cap.release()
    #     logging.info(f"Image saved successfully via OpenCV to {output_path}")
    #     return output_path
    # except ImportError:
    #     logging.warning("OpenCV (cv2) library not found. Cannot use USB webcam.")
    #     return None
    # except Exception as e:
    #     logging.error(f"Failed to capture image with OpenCV: {e}")
    #     # Clean up if VideoCapture object exists
    #     try:
    #         if 'cap' in locals() and cap.isOpened():
    #             cap.release()
    #     except Exception as cleanup_e:
    #          logging.error(f"Error during OpenCV cleanup: {cleanup_e}")
    #     return None

    # --- Fallback ---
    logging.error(
        "No RPi camera method (Picamera2 or OpenCV) is uncommented or functional in image_handler.py"
    )
    return None


def _capture_image_linux(output_path=config.TEMP_IMAGE_PATH):
    """Captures an image using webcam on Linux."""
    logging.info("Attempting image capture via webcam on Linux...")

    try:
        import cv2

        # Use 0 for the default camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Cannot open camera via OpenCV.")
            return None

        # Give camera time to initialize and adjust to lighting
        import time

        time.sleep(2)

        # Capture frame
        ret, frame = cap.read()
        if not ret:
            logging.error("Can't receive frame from camera. Exiting.")
            cap.release()
            return None

        # Save the image
        cv2.imwrite(output_path, frame)
        cap.release()
        logging.info(f"Image saved successfully via OpenCV to {output_path}")
        return output_path

    except ImportError:
        logging.warning("OpenCV (cv2) library not found. Cannot use webcam.")
        return None
    except Exception as e:
        logging.error(f"Failed to capture image with OpenCV: {e}")
        return None


def get_image():
    """
    Gets an image, either by capturing it based on platform or asking for a path.

    Returns:
        str: Path to the captured/selected image, or None if failed.
    """
    image_path = None
    if config.PLATFORM == "termux":
        image_path = _capture_image_termux()
    elif config.PLATFORM == "rpi":
        image_path = _capture_image_rpi()
    elif config.PLATFORM == "linux":
        image_path = _capture_image_linux()
    else:
        print(
            f"Automatic image capture not implemented for platform: {config.PLATFORM}"
        )

    if image_path is None:
        try:
            print("\nImage capture failed or not supported.")
            user_path = input(
                "Please enter the path to an image file (or press Enter to cancel): "
            ).strip()
            if user_path and os.path.exists(user_path):
                logging.info(f"Using user-provided image path: {user_path}")
                # You might want to copy this to a standard temp path
                # For simplicity, we'll use the provided path directly here
                # but be mindful of permissions and cleanup if necessary.
                return user_path
            elif user_path:
                print(f"Error: File not found at '{user_path}'")
                logging.warning(f"User provided non-existent path: {user_path}")
                return None
            else:
                logging.info("User cancelled providing image path.")
                return None
        except Exception as e:
            logging.error(f"Error getting image path from user: {e}")
            return None

    return image_path  # Return path from capture or None

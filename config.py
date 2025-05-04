import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Ensure API key is present
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables or .env file.")

VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemini-1.5-flash") # Updated default
TEXT_MODEL_NAME = os.getenv("TEXT_MODEL_NAME", "gemini-1.5-flash") # Updated default

# Platform and temp file settings
PLATFORM = os.getenv(
    "PLATFORM",
    (
        "termux"
        if os.path.exists("/data/data/com.termux/files/usr/bin/termux-info")
        else "linux" # Default to linux if not termux
        # Add checks for 'rpi', 'windows', 'macos' if needed explicitly
    ),
)
# BOT_NAME = os.getenv("BOT_NAME", "Orka") # Removed, will use persona name

# Set temp path based on detected platform
# Default to /tmp if platform detection is complex or fails
temp_dir = "/tmp"
if PLATFORM == "termux":
    # Termux-specific temp directory
    termux_tmp = "/data/data/com.termux/files/usr/tmp"
    if os.path.isdir(termux_tmp):
        temp_dir = termux_tmp
    else:
        # Fallback within Termux if standard tmp isn't writable/exists
        termux_home_tmp = "/data/data/com.termux/files/home/tmp"
        os.makedirs(termux_home_tmp, exist_ok=True)
        temp_dir = termux_home_tmp
elif PLATFORM in ["linux", "rpi", "macos"]:
    temp_dir = "/tmp"
elif PLATFORM == "windows":
    temp_dir = os.getenv("TEMP", "C:\\Temp") # Use TEMP env var or default

TEMP_IMAGE_PATH = os.getenv(
    "TEMP_IMAGE_PATH",
    os.path.join(temp_dir, "orka_temp_image.jpg") # Use os.path.join
)

# Microphone device index (can be set dynamically)
MIC_DEVICE_INDEX = os.getenv("MIC_DEVICE_INDEX")
if MIC_DEVICE_INDEX is not None:
    try:
        MIC_DEVICE_INDEX = int(MIC_DEVICE_INDEX)
    except ValueError:
        print(f"Warning: Invalid MIC_DEVICE_INDEX '{MIC_DEVICE_INDEX}'. Using default.")
        MIC_DEVICE_INDEX = None


# Safety settings for the models
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

# Persona selection (can be overridden by environment variable)
# Example: export ACTIVE_PERSONA_NAME=HELPER
#  MAIN DEFAULT PERSONA
ACTIVE_PERSONA_NAME = os.getenv("ACTIVE_PERSONA_NAME", "HELPER") # Default to HELPER
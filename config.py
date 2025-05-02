import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemini-2.0-flash")
TEXT_MODEL_NAME = os.getenv("TEXT_MODEL_NAME", "gemini-2.0-flash")

# Platform and temp file settings
PLATFORM = os.getenv(
    "PLATFORM",
    (
        "termux"
        if os.path.exists("/data/data/com.termux/files/usr/bin/termux-info")
        else "linux"
    ),
)
BOT_NAME = os.getenv("BOT_NAME", "Orka")


# This is for the upgrade , wait and watch babyy!
# AGENT_PERSONA = os.getenv("AGENT_PERSONA", "helpful AI assistant")


# # default persona

# DEFAULT_PERSONA = {
#     "name": BOT_NAME,
#     "personality": "helpful and informative",
#     "style": "conversational",
#     "safety_level": "medium"  # low, medium, high
# }


# Set temp path based on detected platform
MIC_DEVICE_INDEX = None  # Will be set dynamically when neededAGENT_PERSONA = os.getenv("AGENT_PERSONA", "helpful AI assistant")


# # default persona

# DEFAULT_PERSONA = {
#     "name": BOT_NAME,
#     "personality": "helpful and informative",
#     "style": "conversational",
#     "safety_level": "medium"  # low, medium, high
# }

TEMP_IMAGE_PATH = os.getenv(
    "TEMP_IMAGE_PATH",
    (
        "/data/data/com.termux/files/usr/tmp/roastyy_temp_image.jpg"
        if PLATFORM == "termux"
        else "/tmp/roastyy_temp_image.jpg"
    ),
)


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

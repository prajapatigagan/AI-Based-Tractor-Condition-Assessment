import os
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# quality thresholds
MIN_RESOLUTION = 480
BLUR_THRESHOLD = 100
MIN_BRIGHTNESS = 50
MAX_BRIGHTNESS = 220

# LLM settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
VISION_MODEL = "openai/gpt-4o-mini"
CHAT_MODEL = "openrouter/free"

# photo slots (key, label)
PHOTO_SLOTS = [
    ("front", "Front"),
    ("rear", "Rear"),
    ("left", "Left side"),
    ("right", "Right side"),
    ("engine", "Engine"),
    ("tyres", "Tyres"),
    ("cabin", "Cabin"),
    ("hourmeter", "Hour meter"),
]
SLOT_LABELS = dict(PHOTO_SLOTS)
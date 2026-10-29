"""
Configuration and Application Constants for Multimodal Attendance & Engagement Agent.
All settings are locally contained and privacy-first.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "classroom_intelligence.db"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
EXPORTS_DIR = DATA_DIR / "exports"
UPLOADS_DIR = DATA_DIR / "temp_uploads"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Processing Defaults
DEFAULT_SAMPLING_INTERVAL_SEC = 1.0  # Sample 1 frame per second
MIN_SAMPLING_INTERVAL_SEC = 0.5
MAX_SAMPLING_INTERVAL_SEC = 5.0
MAX_UPLOAD_SIZE_MB = 200

# Video & Face Detection Defaults
FACE_DETECTOR_CONFIDENCE = 0.5
TRACKING_MAX_DISAPPEARED = 10  # frames a track can be missing before being marked lost
TRACKING_DISTANCE_THRESHOLD = 80.0  # max Euclidean pixel distance for centroid matching

# Attendance Rules
# Sustained presence: participant must be observed in at least 5 frames or sustained for >= 30% of session
MIN_FRAMES_SUSTAINED = 5
SUSTAINED_PERCENTAGE_THRESHOLD = 0.30  # 30% of total session time to be "Present"
PARTIAL_PERCENTAGE_THRESHOLD = 0.10    # 10% to 30% is "Partial", below 10% is "Absent"

# Engagement Proxy Weights (Default when all signals available)
WEIGHT_PRESENCE = 0.35
WEIGHT_MOTION = 0.25
WEIGHT_AUDIO = 0.25
WEIGHT_GAZE = 0.15

# Privacy & Retention
DEFAULT_AUTO_CLEANUP_TEMP = True
ALLOW_TRACK_IMAGE_CACHE = False  # Never cache face crops by default

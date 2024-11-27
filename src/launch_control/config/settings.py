# src/launch_control/config/settings.py

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Audio settings
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 44100))
CHANNELS = int(os.getenv('CHANNELS', 1))
AUDIO_DEVICE_INDEX = int(os.getenv('AUDIO_DEVICE_INDEX', 1))  # Default, should be configurable
AUDIO_THRESHOLD = float(os.getenv('AUDIO_THRESHOLD', 0.005))  # Updated threshold to match .env
SILENCE_THRESHOLD = float(os.getenv('SILENCE_THRESHOLD', 1.0))  # Renamed from SILENCE_DURATION_THRESHOLD
MIN_RECORDING_DURATION = float(os.getenv('MIN_RECORDING_DURATION', 0.5))
MAX_RECORDING_DURATION = float(os.getenv('MAX_RECORDING_DURATION', 30.0))
PRE_ROLL_DURATION = float(os.getenv('PRE_ROLL_DURATION', 0.5))
POST_ROLL_DURATION = float(os.getenv('POST_ROLL_DURATION', 0.5))

# Transcription service configuration
# Options: 'google-chirp', 'openai-whisper'
TRANSCRIPTION_SERVICE_TYPE = os.getenv('TRANSCRIPTION_SERVICE_TYPE', 'google-chirp')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Required if TRANSCRIPTION_SERVICE_TYPE is 'openai-whisper'

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Logging Configuration
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
LOG_FILE = LOGS_DIR / "launch_control.log"

# Project Paths
TRANSCRIPTIONS_DIR = os.getenv('TRANSCRIPTIONS_DIR', 'data/transcriptions')
AUDIO_DIR = os.getenv('AUDIO_DIR', 'data/audio')

# Launch Control

Launch Control is a Python-based application that provides real-time radio capture and transcription using Google Chirp and Gemini API. 

## Features

- Real-time radio capture from configurable input devices
- Asynchronous processing using `asyncio`
- Integration with Google Chirp and Gemini API for transcription
- Configurable audio settings (sample rate, channels, thresholds)
- Comprehensive logging system
- Secure configuration management via environment variables

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/jmcdice/launch-control.git
cd launch-control
```

2. Set up your environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. Configure your environment:
```bash
gcloud init
gcloud auth application-default login
cp .env.example .env
# Edit .env with your API keys and settings
```

4. Run the application:
```bash
bash run.sh
```

## Requirements

- Python 3.7+
- Google Cloud Account 
- Gemini API Key
- Virtual Environment (venv)

## Configuration

Key environment variables in `.env`:

- `TRANSCRIPTION_SERVICE_TYPE`: Choose between 'google-chirp' or 'openai-whisper'
- `GEMINI_API_KEY`: Your Gemini API key
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `AUDIO_DEVICE_INDEX`: Index of your audio input device
- `SAMPLE_RATE`: Audio sample rate (default: 44100)
- `CHANNELS`: Number of audio channels (default: 1)


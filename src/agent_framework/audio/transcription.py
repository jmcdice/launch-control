# src/agent_framework/audio/transcription.py

from abc import ABC, abstractmethod
import io
from typing import Optional
from dataclasses import dataclass
import soundfile as sf
import logging
import openai  # Ensure openai is imported
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

@dataclass
class TranscriptionConfig:
    """Base configuration for transcription services."""
    sample_rate: int = 44100
    language: str = "en-US"
    debug_mode: bool = False
    project_id: Optional[str] = None  # For Google Chirp
    api_key: Optional[str] = None      # For OpenAI Whisper

@dataclass
class TranscriptionResult:
    """Standardized transcription result."""
    text: str
    confidence: float = 1.0
    language: str = "en-US"
    metadata: dict = None

class TranscriptionService(ABC):
    """Abstract base class for transcription services."""

    def __init__(self, config: TranscriptionConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize any required clients or resources."""
        pass

    @abstractmethod
    async def transcribe(self, audio_data) -> Optional[TranscriptionResult]:
        """Transcribe audio data to text."""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources. Override if needed."""
        pass

    def _prepare_audio(self, audio_data) -> io.BytesIO:
        """Convert numpy array to WAV format."""
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, self.config.sample_rate,
                format='WAV', subtype='PCM_16')
        audio_buffer.seek(0)
        return audio_buffer

class GoogleChirpService(TranscriptionService):
    """Google Cloud Chirp transcription service."""

    async def initialize(self) -> None:
        if not self.config.project_id:
            raise ValueError("project_id must be set for GoogleChirpService")

        self.client = SpeechClient(
            client_options=ClientOptions(
                api_endpoint="us-central1-speech.googleapis.com",
            )
        )

    async def transcribe(self, audio_data) -> Optional[TranscriptionResult]:
        try:
            audio_content = self._prepare_audio(audio_data).read()

            config = cloud_speech.RecognitionConfig(
                auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
                language_codes=[self.config.language],
                model="chirp",
            )

            request = cloud_speech.RecognizeRequest(
                recognizer=f"projects/{self.config.project_id}/locations/us-central1/recognizers/_",
                config=config,
                content=audio_content,
            )

            self.logger.debug("Sending audio to Google Chirp...")
            response = self.client.recognize(request=request)

            if response.results:
                result = response.results[0].alternatives[0]
                return TranscriptionResult(
                    text=result.transcript.strip(),
                    confidence=result.confidence,
                    language=self.config.language
                )

            return None

        except Exception as e:
            self.logger.error(f"Google Chirp transcription error: {e}")
            return None

class OpenAIWhisperService(TranscriptionService):
    """OpenAI Whisper transcription service."""

    async def initialize(self) -> None:
        if not self.config.api_key:
            raise ValueError("api_key must be set for OpenAIWhisperService")
        openai.api_key = self.config.api_key
        self.client = openai

    async def transcribe(self, audio_data) -> Optional[TranscriptionResult]:
        try:
            audio_buffer = self._prepare_audio(audio_data)
            audio_buffer.name = 'audio.wav'  # Required by OpenAI

            self.logger.debug("Sending audio to Whisper...")
            response = self.client.Audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer,
                language=self.config.language.split('-')[0]  # Convert en-US to en
            )

            return TranscriptionResult(
                text=response['text'].strip(),
                language=self.config.language
            )

        except Exception as e:
            self.logger.error(f"Whisper transcription error: {e}")
            return None

# Factory for creating transcription services
def create_transcription_service(service_type: str, config: TranscriptionConfig) -> TranscriptionService:
    """Factory function to create transcription services."""
    services = {
        'google-chirp': GoogleChirpService,
        'openai-whisper': OpenAIWhisperService
    }

    if service_type not in services:
        raise ValueError(f"Unknown service type: {service_type}")

    return services[service_type](config)

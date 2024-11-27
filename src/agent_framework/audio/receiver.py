# src/agent_framework/audio/receiver.py

from typing import Optional, Callable, Any
import numpy as np
import sounddevice as sd
import soundfile as sf
import asyncio
import logging
import os
from datetime import datetime
from dataclasses import dataclass

# Import transcription services
from agent_framework.audio.transcription import (
    TranscriptionConfig,
    TranscriptionResult,
    create_transcription_service,
    TranscriptionService
)

@dataclass
class AudioConfig:
    sample_rate: int = 44100
    channels: int = 1
    device_index: int = 1
    audio_threshold: float = 0.005
    silence_threshold: float = 1.0
    min_duration: float = 0.5
    max_duration: float = 30.0
    pre_roll: float = 0.5
    post_roll: float = 0.5
    queue_size: int = 100
    project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT")
    transcription_service_type: str = 'google-chirp'
    api_key: Optional[str] = None

class AudioReceiver:
    """Audio receiving component for transcription."""

    def __init__(
        self,
        config: AudioConfig,
        on_transcription: Callable[[str], Any],
        debug_mode: bool = False
    ):
        self.config = config
        self.on_transcription = on_transcription
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("AudioReceiver")

        # Initialize asyncio queues and flags
        self.audio_queue = asyncio.Queue(maxsize=config.queue_size)
        self.terminate_flag = asyncio.Event()

        # Initialize transcription service
        transcription_config = TranscriptionConfig(
            sample_rate=config.sample_rate,
            language="en-US",
            debug_mode=debug_mode,
            project_id=config.project_id,
            api_key=config.api_key
        )
        self.transcription_service: TranscriptionService = create_transcription_service(
            config.transcription_service_type,
            transcription_config
        )

        # Initialize recording state
        self.pre_roll_buffer = []
        self.recording = False
        self.audio_frames = []
        self.silence_counter = 0.0
        self.recording_duration = 0.0

        # Reference to the event loop
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self):
        """Start the audio receiver."""
        try:
            # Get the running event loop
            self.loop = asyncio.get_running_loop()

            await self.transcription_service.initialize()
            await self._test_audio_input()

            # Start processing task
            asyncio.create_task(self._process_audio_queue())

            # Start audio stream
            self.stream = sd.InputStream(
                device=self.config.device_index,
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype='float32',
                callback=self._audio_callback
            )
            self.stream.start()
            self.logger.info("Audio stream started")

        except Exception as e:
            self.logger.error(f"Error starting audio receiver: {e}")
            raise

    async def stop(self):
        """Stop the audio receiver."""
        self.terminate_flag.set()
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        await self.transcription_service.cleanup()
        self.logger.info("Audio receiver stopped")

    async def _process_audio_queue(self):
        """Process audio data from the queue."""
        while not self.terminate_flag.is_set():
            try:
                audio_data = await self.audio_queue.get()
                if audio_data is not None:
                    await self._transcribe_audio(audio_data)
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")

    def _audio_callback(self, indata, frames, time_info, status):
        """Handle incoming audio data."""
        if status:
            self.logger.warning(f"Audio stream status: {status}")

        rms = np.sqrt(np.mean(np.square(indata)))

        # Update pre-roll buffer
        self.pre_roll_buffer.append(indata.copy())
        pre_roll_frames = int(self.config.pre_roll * self.config.sample_rate / frames)
        if len(self.pre_roll_buffer) > pre_roll_frames:
            self.pre_roll_buffer.pop(0)

        if not self.recording and rms > self.config.audio_threshold:
            self._start_recording()

        if self.recording:
            self._handle_recording(indata, rms, frames)

    def _start_recording(self):
        """Start a new recording."""
        self.recording = True
        self.audio_frames = self.pre_roll_buffer.copy()
        self.silence_counter = 0.0
        self.recording_duration = 0.0
        self.logger.debug("Started recording")

    def _handle_recording(self, indata, rms, frames):
        """Handle ongoing recording state."""
        self.audio_frames.append(indata.copy())
        frame_duration = frames / self.config.sample_rate
        self.recording_duration += frame_duration

        if rms <= self.config.audio_threshold:
            self.silence_counter += frame_duration
        else:
            self.silence_counter = 0.0

        if self._should_stop_recording():
            self._stop_recording()

    def _should_stop_recording(self) -> bool:
        """Determine if recording should stop."""
        return (
            (self.silence_counter >= self.config.silence_threshold or
             self.recording_duration >= self.config.max_duration) and
            self.recording_duration >= self.config.min_duration
        )

    def _stop_recording(self):
        """Stop recording and queue audio for processing."""
        self.recording = False
        audio_data = np.concatenate(self.audio_frames)
        try:
            if self.loop is not None and not self.audio_queue.full():
                # Schedule the coroutine safely in the event loop
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.audio_queue.put(audio_data))
                )
                self.logger.debug("Queued audio for processing")
            else:
                self.logger.warning("Audio queue full or event loop not set, dropping audio frame")
        except RuntimeError as e:
            self.logger.error(f"Failed to enqueue audio data: {e}")
        self.audio_frames = []

    async def _transcribe_audio(self, audio_data):
        """Transcribe audio using the configured service."""
        try:
            self.logger.debug("Sending audio to Google Chirp...")
            # Example of making a request (ensure your transcription service implements this)
            # self.logger.debug(f"Making request: POST https://example.com/transcribe")
            # ... transcription logic ...

            result: Optional[TranscriptionResult] = await self.transcription_service.transcribe(audio_data)
            if result and result.text:
                self.logger.debug(f"Transcribed: {result.text}")
                await self.on_transcription(result.text)  # Await the coroutine
                if self.debug_mode:
                    self._save_debug_data(audio_data, result.text)
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")

    async def _test_audio_input(self):
        """Test audio input configuration."""
        duration = 2
        self.logger.info(f"Testing audio input for {duration} seconds...")

        recording = sd.rec(
            int(duration * self.config.sample_rate),
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            device=self.config.device_index,
            dtype='float32'
        )
        sd.wait()
        rms = np.sqrt(np.mean(np.square(recording)))

        self.logger.info(f"Current RMS level: {rms:.6f}")
        self.logger.info(f"Audio threshold: {self.config.audio_threshold:.6f}")

        if rms < 0.001:
            self.logger.warning("Very low audio levels detected")
        else:
            self.logger.info("Audio input test passed")

    def _save_debug_data(self, audio_data, transcription):
        """Save debug information to disk."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_dir = "debug/audio"
        os.makedirs(debug_dir, exist_ok=True)

        # Save audio
        audio_path = f"{debug_dir}/audio_{timestamp}.wav"
        sf.write(audio_path, audio_data, self.config.sample_rate)

        # Save transcription
        trans_path = f"{debug_dir}/trans_{timestamp}.txt"
        with open(trans_path, 'w') as f:
            f.write(transcription)

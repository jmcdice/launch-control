# src/launch_control/agents/deployment_agent.py

from typing import Optional, Dict, Any
import asyncio
from agent_framework.core.base_agent import BaseAgent, AgentState, Message
from agent_framework.audio.receiver import AudioReceiver, AudioConfig
from datetime import datetime
import logging

class DeploymentAgent(BaseAgent):
    """Basic deployment agent implementation."""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.logger = logging.getLogger(f"deployment_agent.{agent_id}")
        self.audio_receiver: Optional[AudioReceiver] = None
        self.gemini_api_key: Optional[str] = None

    async def initialize(self):
        """Initialize the agent."""
        self.logger.debug("Initializing DeploymentAgent...")
        await self._load_persona()
        await self._setup_audio_components()

    async def _setup_audio_components(self):
        """Initialize audio components."""
        # Initialize AudioConfig with all necessary parameters
        audio_config = AudioConfig(
            sample_rate=self.config.get('sample_rate', 44100),
            channels=self.config.get('channels', 1),
            device_index=self.config.get('audio_device_index', 1),
            audio_threshold=self.config.get('audio_threshold', 0.005),
            silence_threshold=self.config.get('silence_threshold', 1.0),
            min_duration=self.config.get('min_duration', 0.5),
            max_duration=self.config.get('max_duration', 30.0),
            pre_roll=self.config.get('pre_roll', 0.5),
            post_roll=self.config.get('post_roll', 0.5),
            project_id=self.config.get('project_id'),
            transcription_service_type=self.config.get('transcription_service_type', 'google-chirp'),
            api_key=self.config.get('openai_api_key')
        )

        # Initialize AudioReceiver with the updated AudioConfig
        self.audio_receiver = AudioReceiver(
            config=audio_config,
            on_transcription=self._handle_transcription,
            debug_mode=self.config.get('debug', False)
        )

        # Store Gemini API key for later use in processing
        self.gemini_api_key = self.config.get('gemini_api_key')

    async def _load_persona(self):
        """Load agent persona configuration."""
        # For now, just use a basic persona
        self.persona = {
            "name": "Launch Control",
            "description": "A helpful deployment assistant"
        }

    async def process_input(self, input_data: Any) -> Optional[str]:
        """Process incoming transcribed text."""
        if not isinstance(input_data, str):
            return None

        # For now, just echo back what was heard
        return f"Received: {input_data}"

    async def _handle_transcription(self, text: str):
        """Handle incoming transcription."""
        # Log the transcription
        self.logger.info(f"Transcribed: {text}")

        # Add to conversation history
        message = Message(
            content=text,
            timestamp=datetime.now(),
            sender="user"
        )
        self.conversation_history.add_message(message)

        # Process the input
        response = await self.process_input(text)
        if response:
            await self._send_response(response)

    async def _receive_input(self) -> Optional[Any]:
        """Not actively used since we're using callback-based audio receiver."""
        await asyncio.sleep(0.1)
        return None

    async def _send_response(self, response: str):
        """Handle sending responses."""
        # For now, just log the response
        self.logger.info(f"Response: {response}")

        # Add to conversation history
        message = Message(
            content=response,
            timestamp=datetime.now(),
            sender=self.agent_id
        )
        self.conversation_history.add_message(message)

    async def start(self):
        """Start the agent's main functionality."""
        self.logger.debug("Starting DeploymentAgent...")
        # Start the AudioReceiver
        await self.audio_receiver.start()
        # Add any additional startup tasks here if needed

    async def stop(self):
        """Stop the agent's main functionality."""
        self.logger.debug("Stopping DeploymentAgent...")
        if self.audio_receiver:
            await self.audio_receiver.stop()
        # Stop any other components or tasks here if necessary

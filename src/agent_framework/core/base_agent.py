# src/agent_framework/core/base_agent.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import logging
from datetime import datetime

class AgentState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ERROR = "error"

@dataclass
class Message:
    content: str
    timestamp: datetime
    sender: str
    metadata: Dict[str, Any] = None

class ConversationHistory:
    def __init__(self, max_length: int = 100):
        self.messages: List[Message] = []
        self.max_length = max_length
    
    def add_message(self, message: Message):
        self.messages.append(message)
        if len(self.messages) > self.max_length:
            self.messages.pop(0)
    
    def get_recent_messages(self, count: int) -> List[Message]:
        return self.messages[-count:]

class BaseAgent(ABC):
    """Base class for all agents in the Launch Control framework."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.state = AgentState.IDLE
        self.conversation_history = ConversationHistory()
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Initialize components
        self.audio_receiver = None
        self.audio_transmitter = None
        
    async def initialize(self):
        """Initialize agent components and connections."""
        try:
            await self._setup_audio_components()
            await self._load_persona()
            self.state = AgentState.IDLE
            self.logger.info(f"Agent {self.agent_id} initialized successfully")
        except Exception as e:
            self.state = AgentState.ERROR
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            raise
    
    @abstractmethod
    async def _setup_audio_components(self):
        """Set up audio receiving and transmitting components."""
        pass
    
    @abstractmethod
    async def _load_persona(self):
        """Load agent persona and related configurations."""
        pass
    
    @abstractmethod
    async def process_input(self, input_data: Any) -> Optional[str]:
        """Process incoming data and generate a response."""
        pass
    
    async def start(self):
        """Start the agent's main processing loop."""
        self.state = AgentState.LISTENING
        try:
            while True:
                if self.state == AgentState.LISTENING:
                    input_data = await self._receive_input()
                    if input_data:
                        self.state = AgentState.PROCESSING
                        response = await self.process_input(input_data)
                        if response:
                            self.state = AgentState.RESPONDING
                            await self._send_response(response)
                        self.state = AgentState.LISTENING
                await asyncio.sleep(0.1)
        except Exception as e:
            self.state = AgentState.ERROR
            self.logger.error(f"Agent error: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the agent and cleanup resources."""
        self.state = AgentState.IDLE
        if self.audio_receiver:
            await self.audio_receiver.cleanup()
        if self.audio_transmitter:
            await self.audio_transmitter.cleanup()
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    @abstractmethod
    async def _receive_input(self) -> Optional[Any]:
        """Receive and preprocess input data."""
        pass
    
    @abstractmethod
    async def _send_response(self, response: str):
        """Send agent response through appropriate channel."""
        pass
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update agent configuration."""
        self.config.update(new_config)
        self.logger.info("Agent configuration updated")
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state
    
    def get_conversation_history(self, message_count: int = None) -> List[Message]:
        """Get recent conversation history."""
        if message_count is None:
            return self.conversation_history.messages
        return self.conversation_history.get_recent_messages(message_count)

class AgentException(Exception):
    """Base exception class for agent-related errors."""
    pass

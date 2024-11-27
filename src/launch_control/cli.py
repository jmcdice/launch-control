# src/launch_control/cli.py

import click
import asyncio
import signal
import logging
from pathlib import Path
import sys
from dotenv import load_dotenv
import os  # Ensure os is imported

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Explicitly import required settings
from launch_control.config.settings import (
    SAMPLE_RATE,
    CHANNELS,
    AUDIO_DEVICE_INDEX,
    AUDIO_THRESHOLD,
    SILENCE_THRESHOLD,
    MIN_RECORDING_DURATION,
    MAX_RECORDING_DURATION,
    PRE_ROLL_DURATION,
    POST_ROLL_DURATION,
    LOG_FORMAT,
    LOG_FILE,
    TRANSCRIPTION_SERVICE_TYPE,
    OPENAI_API_KEY
)
from launch_control.agents.deployment_agent import DeploymentAgent

def setup_logging(debug: bool):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

@click.group()
def cli():
    """Launch Control CLI"""
    pass

@cli.command()
@click.option('--debug', is_flag=True, help='Enable debug mode')
def listen(debug):
    """Start the listener agent."""
    setup_logging(debug)

    # Validate required credentials
    if not os.getenv('GOOGLE_CLOUD_PROJECT'):
        click.echo("Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        sys.exit(1)

    if not os.getenv('GEMINI_API_KEY'):
        click.echo("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    # Create agent configuration
    config = {
        'sample_rate': SAMPLE_RATE,
        'channels': CHANNELS,
        'audio_device_index': AUDIO_DEVICE_INDEX,
        'audio_threshold': AUDIO_THRESHOLD,
        'silence_threshold': SILENCE_THRESHOLD,
        'min_duration': MIN_RECORDING_DURATION,
        'max_duration': MAX_RECORDING_DURATION,
        'pre_roll': PRE_ROLL_DURATION,
        'post_roll': POST_ROLL_DURATION,
        'debug': debug,
        'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'transcription_service_type': TRANSCRIPTION_SERVICE_TYPE,
        'openai_api_key': OPENAI_API_KEY
    }

    # Debug: Print configuration if in debug mode
    if debug:
        logging.debug(f"Agent Configuration: {config}")

    async def main():
        agent = DeploymentAgent("listener", config)
        await agent.initialize()
        try:
            # Start the agent
            await agent.start()
            # click.echo("Starting listener...")

            # Create an asyncio Event to wait on
            stop_event = asyncio.Event()

            # Define a handler for termination signals
            def handle_exit(sig):
                logging.info(f"Received exit signal {sig.name}...")
                stop_event.set()

            # Register signal handlers
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, lambda s=sig: handle_exit(s))
                except NotImplementedError:
                    # Signal handling might not be implemented on some platforms (e.g., Windows)
                    logging.warning(f"Signal handling for {sig.name} is not implemented on this platform.")

            # Wait until a termination signal is received
            await stop_event.wait()

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            await agent.stop()
            logging.info("Listener stopped gracefully.")

    # Run the main coroutine
    asyncio.run(main())

if __name__ == '__main__':
    cli()


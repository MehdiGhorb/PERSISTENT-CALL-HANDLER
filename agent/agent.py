#!/usr/bin/env python3
"""
Persistent Agent Worker
Runs continuously, handles incoming calls on assigned phone number
"""
import asyncio
import os
import sys
import signal
import time

from livekit import rtc
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero, deepgram, cartesia

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from services.logging_config import setup_logging, get_logger

# Get phone number from environment variable set by agent manager
PHONE_NUMBER = os.getenv("AGENT_PHONE_NUMBER", "")

class ConfigurableAgent(Agent):
    """Voice Agent for persistent call handling"""
    
    def __init__(self, phone_number: str):
        settings = get_settings()
        
        # Build system instructions
        instructions = f"""{settings.agent_prompt}

IMPORTANT CONTEXT:
- Phone Number: {phone_number}
- Timezone: {settings.timezone}
- Language: {settings.language} (respond in this language)
- Keep responses natural and conversational for voice interaction
- No special formatting, emojis, or complex punctuation"""
        
        super().__init__(instructions=instructions)
        self.phone_number = phone_number
        self.settings = settings
        self.logger = get_logger(f"Agent-{phone_number}")

async def entrypoint(ctx: JobContext):
    """Main entry point for handling incoming calls"""
    logger = get_logger(f"Agent-{PHONE_NUMBER}")
    logger.info(f"📞 Incoming call on {PHONE_NUMBER}")
    logger.info(f"🏠 Room: {ctx.room.name}")
    
    # Create agent
    agent = ConfigurableAgent(PHONE_NUMBER)
    settings = get_settings()
    
    logger.info(f"🤖 Creating session with LLM: {settings.llm_model}, Voice: {settings.voice}")
    
    # Configure TTS
    if settings.tts_provider == "cartesia" and settings.cartesia_api_key:
        tts = cartesia.TTS(
            voice=settings.voice,
            language="en"  # You can make this configurable based on settings.language
        )
    else:
        tts = openai.TTS(voice="alloy")
    
    # Configure STT
    if settings.stt_provider == "deepgram" and settings.deepgram_api_key:
        stt = deepgram.STT(language="en")
    else:
        stt = openai.STT()
    
    # Create session with explicit components
    session = AgentSession(
        stt=stt,
        llm=openai.LLM(model=settings.llm_model),
        tts=tts,
        vad=silero.VAD.load(),
    )
    
    logger.info(f"🔗 Starting session...")
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=agent
    )
    
    logger.info(f"✅ Session started successfully")
    
    # Generate initial greeting to make agent speak first
    await session.generate_reply(
        instructions="Start the conversation by greeting the user as specified in your instructions."
    )
    
    logger.info(f"✅ Agent is now active and handling the call!")

def prewarm(proc: JobContext):
    """Prewarm function to initialize models before first call"""
    logger = get_logger(__name__)
    logger.info("⚡ Prewarming agent...")

if __name__ == "__main__":
    # Setup logging
    settings = get_settings()
    setup_logging(log_level=settings.log_level)
    logger = get_logger(__name__)
    
    if not PHONE_NUMBER:
        logger.error("AGENT_PHONE_NUMBER environment variable not set")
        sys.exit(1)
    
    logger.info(f"🚀 Starting agent for {PHONE_NUMBER}")
    
    # Get port from environment (set by agent manager)
    agent_port = int(os.getenv("LIVEKIT_AGENT_HTTP_PORT", "8081"))
    logger.info(f"Agent HTTP port: {agent_port}")
    
    # Run with LiveKit CLI with specific port
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name=f"persistent-agent-{PHONE_NUMBER.replace('+', '')}",
            port=agent_port
        )
    )

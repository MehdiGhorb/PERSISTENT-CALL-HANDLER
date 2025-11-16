"""
Persistent Call Handler - Main API Service
Production-ready backend for always-on phone agents
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from config import get_settings
from services.logging_config import setup_logging, get_logger
from services.livekit_manager import livekit_manager
from services.agent_manager import agent_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    settings = get_settings()
    logger = get_logger(__name__)
    
    # Setup logging
    setup_logging(log_level=settings.log_level)
    
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 PERSISTENT CALL HANDLER - STARTING")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Host: {settings.api_host}")
    logger.info(f"API Port: {settings.api_port}")
    logger.info(f"PORT env var: {os.getenv('PORT', 'not set')}")
    logger.info(f"API URL: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"Phone Numbers: {', '.join(settings.phone_numbers)}")
    
    # Initialize LiveKit
    logger.info("Initializing LiveKit SIP Manager...")
    livekit_ok = await livekit_manager.initialize()
    if not livekit_ok:
        raise RuntimeError("Failed to initialize LiveKit")
    
    # Setup phone numbers with SIP trunks and dispatch rules
    logger.info("Setting up phone number routing...")
    for phone_number in settings.phone_numbers:
        agent_name = f"persistent-agent-{phone_number.replace('+', '')}"
        setup_ok = await livekit_manager.setup_phone_number(phone_number, agent_name)
        if not setup_ok:
            raise RuntimeError(f"Failed to setup {phone_number}")
    
    # Start agent processes
    logger.info("Starting agent processes...")
    await agent_manager.start()
    
    # Wait for agents to be ready
    logger.info("Waiting for agents to initialize...")
    await asyncio.sleep(5)
    
    logger.info("=" * 60)
    logger.info("✅ PERSISTENT CALL HANDLER - READY")
    logger.info(f"📞 {len(settings.phone_numbers)} phone numbers are now live and ready to receive calls")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await agent_manager.stop()
    logger.info("✅ Shutdown complete")

app = FastAPI(
    title="Persistent Call Handler",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Persistent Call Handler",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    
    # Get agent status
    agent_status = await agent_manager.get_status()
    
    # Get LiveKit health
    livekit_health = await livekit_manager.health_check()
    
    all_healthy = all(
        status["running"] for status in agent_status.values()
    ) and all(livekit_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "phone_numbers": settings.phone_numbers,
        "agents": agent_status,
        "livekit": livekit_health
    }

@app.get("/status")
async def get_status():
    """Detailed status endpoint"""
    settings = get_settings()
    agent_status = await agent_manager.get_status()
    livekit_health = await livekit_manager.health_check()
    
    return {
        "service": "Persistent Call Handler",
        "environment": settings.environment,
        "phone_numbers": settings.phone_numbers,
        "agents": agent_status,
        "livekit_trunks": livekit_health,
        "configuration": {
            "llm_model": settings.llm_model,
            "tts_provider": settings.tts_provider,
            "stt_provider": settings.stt_provider,
            "voice": settings.voice,
            "timezone": settings.timezone,
            "language": settings.language
        }
    }

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development"
    )

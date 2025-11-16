"""
Configuration for Persistent Call Handler
"""
import os
import sys
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    # Railway uses PORT env var, fallback to API_PORT or 8001
    api_port: int = Field(default=8001, env="PORT")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # LiveKit Settings (required)
    livekit_api_key: str = Field(env="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(env="LIVEKIT_API_SECRET")
    livekit_url: str = Field(env="LIVEKIT_URL")
    
    # AI Settings (openai is required, others optional)
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    cartesia_api_key: str = Field(default="", env="CARTESIA_API_KEY")
    deepgram_api_key: str = Field(default="", env="DEEPGRAM_API_KEY")
    
    # Phone Numbers - hardcoded for persistence
    phone_numbers: list[str] = ["+3197010255451", "+16506000977"]
    
    # Agent Configuration
    agent_prompt: str = Field(
        default="""You are a helpful voice AI assistant.
You eagerly assist users with their questions.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
You are curious, friendly, and have a sense of humor.""",
        env="AGENT_PROMPT"
    )
    llm_model: str = Field(default="gpt-4o", env="LLM_MODEL")
    voice: str = Field(default="79a125e8-cd45-4c13-8a67-188112f4dd22", env="VOICE")  # Cartesia voice ID
    tts_provider: str = Field(default="cartesia", env="TTS_PROVIDER")
    stt_provider: str = Field(default="deepgram", env="STT_PROVIDER")
    timezone: str = Field(default="gmt+0", env="TIMEZONE")
    language: str = Field(default="English", env="LANGUAGE")
    
    # Health Check Settings
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    agent_startup_timeout: int = Field(default=60, env="AGENT_STARTUP_TIMEOUT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        # Make .env.local optional - use environment variables in production
        env_file = ".env.local" if os.path.exists(".env.local") else None
        case_sensitive = False
        extra = "ignore"

_settings = None

def get_settings() -> Settings:
    """Get settings singleton with better error handling"""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ CONFIGURATION ERROR")
            print("=" * 60)
            print(f"\nError: {e}")
            print("\nRequired environment variables:")
            print("  - LIVEKIT_API_KEY")
            print("  - LIVEKIT_API_SECRET")
            print("  - LIVEKIT_URL")
            print("  - OPENAI_API_KEY")
            print("\nOptional environment variables:")
            print("  - CARTESIA_API_KEY (for Cartesia TTS)")
            print("  - DEEPGRAM_API_KEY (for Deepgram STT)")
            print("\nIn Railway/Render:")
            print("  Set these in the Environment Variables section")
            print("\nFor local development:")
            print("  Create .env.local file with these variables")
            print("=" * 60 + "\n")
            sys.exit(1)
    return _settings

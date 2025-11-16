# Persistent Call Handler ✅ PRODUCTION READY

Always-on backend that keeps your Twilio phone numbers active 24/7 with AI voice agents.

## Phone Numbers
- **+3197010255451** ✅ Active
- **+16506000977** ✅ Active

## Quick Start

```bash
# 1. Configure
cp .env.example .env.local
# Edit .env.local with LiveKit, OpenAI, Cartesia, and Deepgram credentials

# 2. Start
./start.sh

# 3. Check status
curl http://localhost:8001/status | python3 -m json.tool
```

## Features

✅ **Auto-restart** - Agents restart automatically on crash  
✅ **Health monitoring** - 30-second health checks ensure agents stay running  
✅ **Docker** - Production-ready containerization with restart policies  
✅ **SIP routing** - LiveKit SIP trunks and dispatch rules automatically configured  
✅ **Separate ports** - Each agent gets its own port to avoid conflicts  
✅ **Structured logging** - All logs tagged by phone number  

## Architecture

- **FastAPI** (port 8001) - API service with lifecycle management
- **Agent workers** (ports 8081, 8082) - LiveKit voice agents (one per number)
- **LiveKit SIP** - Automatic trunk and dispatch rule setup
- **Auto-recovery** - Crashed agents restart within 30 seconds

## API Endpoints

```bash
GET /              # Service info
GET /health        # Health check (for monitoring)
GET /status        # Detailed status of all agents
```

## How It Works

1. Service starts and configures LiveKit SIP trunks for both phone numbers
2. Creates dispatch rules routing each number to its dedicated agent
3. Spawns agent processes (one per phone number) on separate ports
4. Monitors agent health every 30 seconds
5. Automatically restarts any crashed agents
6. When someone calls your Twilio number → LiveKit routes to agent → AI answers

## Management

```bash
./start.sh    # Start service
./logs.sh     # View logs
./stop.sh     # Stop service

# Docker commands
docker compose ps                  # Check status
docker compose logs -f             # Follow logs
docker compose restart             # Restart service
```

## Production Notes

- Service runs as non-root user for security
- Health checks every 30 seconds
- Docker restart policy: `unless-stopped`
- Resource limits: 2GB RAM, 2 CPUs max
- Log rotation: 10MB max, 3 files

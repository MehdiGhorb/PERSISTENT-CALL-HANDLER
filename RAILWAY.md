# Railway Deployment Guide

## Quick Setup

### 1. Create Railway Project
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project (or create new)
railway link
```

### 2. Set Environment Variables

In Railway dashboard or via CLI:

```bash
# Required Variables
railway variables set LIVEKIT_API_KEY="your_livekit_api_key"
railway variables set LIVEKIT_API_SECRET="your_livekit_api_secret"
railway variables set LIVEKIT_URL="wss://your-livekit-url.livekit.cloud"
railway variables set OPENAI_API_KEY="your_openai_api_key"

# Optional but Recommended (for better voice quality)
railway variables set CARTESIA_API_KEY="your_cartesia_api_key"
railway variables set DEEPGRAM_API_KEY="your_deepgram_api_key"

# Optional Configuration
railway variables set AGENT_PROMPT="Your custom agent prompt"
railway variables set LLM_MODEL="gpt-4o"
railway variables set VOICE="79a125e8-cd45-4c13-8a67-188112f4dd22"
railway variables set TTS_PROVIDER="cartesia"
railway variables set STT_PROVIDER="deepgram"
railway variables set TIMEZONE="gmt+0"
railway variables set LANGUAGE="English"
railway variables set LOG_LEVEL="INFO"
```

### 3. Deploy

```bash
# Deploy from GitHub (recommended)
# - Connect your GitHub repo in Railway dashboard
# - Railway will auto-deploy on push

# OR deploy directly via CLI
railway up
```

### 4. Verify Deployment

```bash
# Check logs
railway logs

# Check status endpoint
curl https://your-app.railway.app/status

# Check health
curl https://your-app.railway.app/health
```

## Environment Variables Reference

### Required
- `LIVEKIT_API_KEY` - Your LiveKit API key
- `LIVEKIT_API_SECRET` - Your LiveKit API secret
- `LIVEKIT_URL` - Your LiveKit WebSocket URL (wss://...)
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional
- `CARTESIA_API_KEY` - For Cartesia TTS (better voice quality)
- `DEEPGRAM_API_KEY` - For Deepgram STT (better speech recognition)
- `AGENT_PROMPT` - Custom system prompt for the agent
- `LLM_MODEL` - LLM model (default: gpt-4o)
- `VOICE` - Cartesia voice ID (default: 79a125e8-cd45-4c13-8a67-188112f4dd22)
- `TTS_PROVIDER` - TTS provider: cartesia or openai (default: cartesia)
- `STT_PROVIDER` - STT provider: deepgram or openai (default: deepgram)
- `TIMEZONE` - Agent timezone (default: gmt+0)
- `LANGUAGE` - Agent language (default: English)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Troubleshooting

### "Field required" errors
- Make sure all required environment variables are set in Railway dashboard
- Check variable names match exactly (case-sensitive)
- Restart the service after setting variables

### Service won't start
- Check logs: `railway logs`
- Verify LiveKit credentials are correct
- Ensure LiveKit URL starts with `wss://`

### Agents not answering calls
- Check status endpoint: `curl https://your-app.railway.app/status`
- Verify both agents show `"running": true`
- Check LiveKit trunks are active
- Review logs for errors

## Support

Check the main README.md for more deployment options and troubleshooting.

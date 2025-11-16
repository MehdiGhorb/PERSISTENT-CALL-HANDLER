"""
Agent Process Manager - Manages persistent agent subprocesses
"""
import asyncio
import subprocess
import sys
import os
from typing import Dict, Optional
from datetime import datetime

from services.logging_config import get_logger
from config import get_settings

class AgentProcess:
    """Represents a running agent subprocess"""
    
    def __init__(self, phone_number: str, process: subprocess.Popen):
        self.phone_number = phone_number
        self.process = process
        self.started_at = datetime.utcnow()
        self.restart_count = 0
        
    def is_running(self) -> bool:
        """Check if process is alive"""
        return self.process.poll() is None
    
    async def stop(self, timeout: int = 10) -> bool:
        """Stop the agent process"""
        if not self.is_running():
            return True
        
        try:
            self.process.terminate()
            
            # Wait for graceful shutdown
            for _ in range(timeout * 10):
                if not self.is_running():
                    return True
                await asyncio.sleep(0.1)
            
            # Force kill if needed
            self.process.kill()
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"Error stopping agent for {self.phone_number}: {e}")
            return False

class AgentManager:
    """Manages lifecycle of agent processes"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.agents: Dict[str, AgentProcess] = {}
        self._lock = asyncio.Lock()
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Get paths
        self.python_executable = sys.executable
        self.agent_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "agent",
            "agent.py"
        )
    
    async def start(self):
        """Start all agents for configured phone numbers"""
        self.logger.info("🚀 Starting Agent Manager...")
        self.running = True
        
        # Verify agent script exists
        if not os.path.exists(self.agent_script):
            raise FileNotFoundError(f"Agent script not found: {self.agent_script}")
        
        # Start agent for each phone number
        for phone_number in self.settings.phone_numbers:
            await self._start_agent(phone_number)
        
        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitor_agents())
        
        self.logger.info("✅ All agents started")
    
    async def _start_agent(self, phone_number: str, is_restart: bool = False) -> bool:
        """Start an agent process"""
        async with self._lock:
            try:
                # Check if already running
                if phone_number in self.agents and self.agents[phone_number].is_running():
                    self.logger.warning(f"Agent for {phone_number} already running")
                    return True
                
                log_prefix = "🔄 Restarting" if is_restart else "🚀 Starting"
                self.logger.info(f"{log_prefix} agent for {phone_number}")
                
                # Assign unique port for this agent (starting from 8081)
                agent_index = self.settings.phone_numbers.index(phone_number)
                agent_port = 8081 + agent_index
                
                # Build environment with all settings
                env = os.environ.copy()
                env.update({
                    "LIVEKIT_URL": self.settings.livekit_url,
                    "LIVEKIT_API_KEY": self.settings.livekit_api_key,
                    "LIVEKIT_API_SECRET": self.settings.livekit_api_secret,
                    "OPENAI_API_KEY": self.settings.openai_api_key,
                    "AGENT_PHONE_NUMBER": phone_number,  # Pass phone number via env var
                    "LIVEKIT_AGENT_HTTP_PORT": str(agent_port),  # Unique port per agent
                })
                
                if self.settings.cartesia_api_key:
                    env["CARTESIA_API_KEY"] = self.settings.cartesia_api_key
                if self.settings.deepgram_api_key:
                    env["DEEPGRAM_API_KEY"] = self.settings.deepgram_api_key
                
                # Start the process with LiveKit CLI command
                process = subprocess.Popen(
                    [self.python_executable, self.agent_script, "start"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Store agent process
                agent_process = AgentProcess(phone_number, process)
                if is_restart and phone_number in self.agents:
                    agent_process.restart_count = self.agents[phone_number].restart_count + 1
                
                self.agents[phone_number] = agent_process
                
                self.logger.info(f"✅ Agent started for {phone_number} (PID: {process.pid}, Port: {agent_port})")
                
                # Start log streaming task
                asyncio.create_task(self._stream_logs(phone_number, process))
                
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Failed to start agent for {phone_number}: {e}")
                return False
    
    async def _stream_logs(self, phone_number: str, process: subprocess.Popen):
        """Stream agent logs to main logger"""
        try:
            loop = asyncio.get_event_loop()
            while True:
                # Read line in a non-blocking way
                line = await loop.run_in_executor(None, process.stdout.readline)
                if not line:
                    # Process ended
                    break
                self.logger.info(f"[{phone_number}] {line.rstrip()}")
        except Exception as e:
            self.logger.error(f"Error streaming logs for {phone_number}: {e}")
    
    async def _monitor_agents(self):
        """Monitor agent health and restart if needed"""
        self.logger.info("👀 Starting agent health monitor")
        
        while self.running:
            try:
                await asyncio.sleep(self.settings.health_check_interval)
                
                for phone_number in self.settings.phone_numbers:
                    agent = self.agents.get(phone_number)
                    
                    if not agent or not agent.is_running():
                        self.logger.warning(f"⚠️ Agent for {phone_number} is down, restarting...")
                        await self._start_agent(phone_number, is_restart=True)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in agent monitor: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("Monitor stopped")
    
    async def stop(self):
        """Stop all agents"""
        self.logger.info("🛑 Stopping all agents...")
        self.running = False
        
        # Cancel monitor task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all agents
        stop_tasks = []
        for agent in self.agents.values():
            stop_tasks.append(agent.stop())
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.agents.clear()
        self.logger.info("✅ All agents stopped")
    
    async def get_status(self) -> Dict:
        """Get status of all agents"""
        status = {}
        for phone_number, agent in self.agents.items():
            status[phone_number] = {
                "running": agent.is_running(),
                "pid": agent.process.pid if agent.is_running() else None,
                "started_at": agent.started_at.isoformat(),
                "restart_count": agent.restart_count
            }
        return status

agent_manager = AgentManager()

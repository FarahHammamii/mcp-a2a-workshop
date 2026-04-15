"""
Run the multi-agent system.
Starts both agents and the MCP server.
"""

import asyncio
import subprocess
import sys
import os
import signal
from typing import List
import time

# Add agents directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.weather_agent import WeatherAgent
from agents.analysis_agent import AnalysisAgent


class MultiAgentSystem:
    """Manages the multi-agent system."""
    
    def __init__(self):
        self.processes = []
        self.weather_agent = None
        self.analysis_agent = None
    
    def start_mcp_server(self):
        """Start MCP server as background process."""
        print("🚀 Starting MCP Weather Server...")
        proc = subprocess.Popen(
            [sys.executable, "mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(proc)
        time.sleep(2)
        print("✅ MCP Server started")
        return proc
    
    async def start_agents(self):
        """Start both A2A agents."""
        print("\n🤖 Starting A2A Agents...")
        
        # Start weather agent
        self.weather_agent = WeatherAgent(port=8001)
        print(f"   - Weather Agent starting on port 8001")
        
        # Start analysis agent
        self.analysis_agent = AnalysisAgent(port=8002, weather_agent_url="http://localhost:8001")
        print(f"   - Analysis Agent starting on port 8002")
        
        # Run agents concurrently
        await asyncio.gather(
            self._run_agent(self.weather_agent),
            self._run_agent(self.analysis_agent)
        )
    
    async def _run_agent(self, agent):
        """Run a single agent."""
        # Keep the agent running until shutdown.
        await agent.run()

    async def cleanup(self):
        """Clean up all resources."""
        print("\n🛑 Shutting down...")
        
        if self.weather_agent:
            await self.weather_agent.cleanup()
        if self.analysis_agent:
            await self.analysis_agent.cleanup()
        
        for proc in self.processes:
            proc.terminate()
            proc.wait()
        
        print("✅ Cleanup complete")


async def main():
    """Main entry point."""
    print("=" * 60)
    print("🌤️  Multi-Agent Weather System with A2A + MCP")
    print("=" * 60)
    print("\nArchitecture:")
    print("  📡 MCP Server (weather tools)")
    print("  🤖 Weather Agent (port 8001) - Fetches weather data")
    print("  📊 Analysis Agent (port 8002) - Analyzes and recommends")
    print("  🔗 A2A Protocol - Agent-to-agent communication")
    print("\n" + "=" * 60)
    
    system = MultiAgentSystem()
    
    try:
        # Start MCP server
        system.start_mcp_server()
        
        # Start agents
        await system.start_agents()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutdown signal received")
    finally:
        await system.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
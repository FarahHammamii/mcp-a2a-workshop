"""
Weather Agent - Uses MCP tools to fetch weather data.
"""

import asyncio
import subprocess
import sys
import os
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from groq import Groq
from langchain_mcp_adapters.client import MultiServerMCPClient

from .base_agent import BaseA2AAgent

load_dotenv()


class WeatherAgent(BaseA2AAgent):
    """
    Weather agent that fetches data using MCP tools.
    This agent uses Groq LLM to understand user queries and call appropriate MCP tools.
    """
    
    def __init__(self, port: int = 8001):
        super().__init__(
            name="Weather Data Agent",
            description="Fetches current weather and forecasts using MCP tools",
            version="1.0.0",
            port=port
        )
        
        # Initialize Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        self.groq_client = Groq(api_key=api_key)
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        # MCP client and tools
        self.mcp_client = None
        self.mcp_tools = []
        self.mcp_process = None
        self.mcp_initialized = False
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                {
                    "id": "get_current_weather",
                    "name": "Current Weather",
                    "description": "Get current weather for any city"
                },
                {
                    "id": "get_weather_forecast",
                    "name": "Weather Forecast",
                    "description": "Get multi-day weather forecast"
                }
            ],
            "mcp_supported": True
        }
    
    async def _start_mcp_server(self):
        """Start the MCP server as a subprocess."""
        try:
            # Find the correct path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            mcp_script = os.path.join(parent_dir, "mcp_server.py")
            
            if not os.path.exists(mcp_script):
                mcp_script = os.path.join(current_dir, "mcp_server.py")
            
            print(f"📍 Starting MCP server from: {mcp_script}")
            
            # Start MCP server
            self.mcp_process = subprocess.Popen(
                [sys.executable, mcp_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            await asyncio.sleep(2)  # Wait for server to start
            
            # Check if process is running
            if self.mcp_process.poll() is not None:
                stderr = self.mcp_process.stderr.read().decode()
                raise Exception(f"MCP server died: {stderr}")

            # Connect to MCP server
            self.mcp_client = MultiServerMCPClient({
                "weather": {
                    "command": sys.executable,
                    "args": [mcp_script],
                    "transport": "stdio",
                }
            })

            # Get tools directly (new API)
            self.mcp_tools = await self.mcp_client.get_tools()
            self.mcp_initialized = True
            
            print(f"✅ Weather Agent: Loaded {len(self.mcp_tools)} MCP tools")
            for tool in self.mcp_tools:
                print(f"   - {tool.name}")
            
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            self.mcp_initialized = False
            raise
    
    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool directly."""
        try:
            print(f"DEBUG: Looking for tool '{tool_name}'")
            
            for tool in self.mcp_tools:
                if tool.name == tool_name:
                    print(f"🔧 Found tool! Calling MCP tool: {tool_name}({arguments})")
                    result = await tool.ainvoke(arguments)
                    print(f"📦 Raw MCP result type: {type(result)}")
                    print(f"📦 Raw MCP result: {result}")

                    # Extract text from the result
                    if isinstance(result, list) and len(result) > 0:
                        # Result is a list of TextContent objects
                        if hasattr(result[0], 'text'):
                            text_content = result[0].text
                            print(f"✅ Extracted text from list: {text_content[:100]}...")
                            return text_content
                        elif isinstance(result[0], dict) and 'text' in result[0]:
                            text_content = result[0]['text']
                            print(f"✅ Extracted text from dict list: {text_content[:100]}...")
                            return text_content
                    
                    elif hasattr(result, 'text'):
                        text_content = result.text
                        print(f"✅ Extracted text from object: {text_content[:100]}...")
                        return text_content
                    
                    elif isinstance(result, str):
                        print(f"✅ Result is string: {result[:100]}...")
                        return result
                    
                    elif isinstance(result, dict) and 'text' in result:
                        print(f"✅ Result is dict with text: {result['text'][:100]}...")
                        return result['text']
                    
                    else:
                        # Fallback: convert to JSON
                        print(f"⚠️ Unknown result format, converting to JSON")
                        return json.dumps(result)
            
            # If we get here, tool wasn't found
            available_tools = [t.name for t in self.mcp_tools]
            return f"Tool '{tool_name}' not found. Available tools: {available_tools}"

        except Exception as e:
            print(f"❌ ERROR calling MCP tool {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e)})
    async def _understand_and_execute(self, user_message: str) -> str:
        """Use Groq to understand the user and execute appropriate MCP tool."""

        if not self.mcp_tools:
            return "MCP tools not available. Please check the MCP server connection."
        
        # Get exact tool names
        tool_names = [t.name for t in self.mcp_tools]
        tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in self.mcp_tools])

        # FIXED: Use exact tool names in the prompt
        prompt = f"""You are a weather assistant. Based on the user's question, call the appropriate MCP tool.

Available tools (use these EXACT names):
{tools_desc}

User question: {user_message}

Respond with ONLY a JSON object. Use the exact tool names from above.

Examples:
- For current weather: {{"tool": "get_current_weather", "arguments": {{"city": "London"}}}}
- For forecast: {{"tool": "get_weather_forecast", "arguments": {{"city": "Tokyo", "days": 5}}}}
- If not about weather: {{"tool": "none", "message": "I can only help with weather queries."}}

IMPORTANT: The tool names are exactly: {', '.join(tool_names)}
"""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )

            content = response.choices[0].message.content.strip()
            print(f"🤖 Groq response: {content}")

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                decision = json.loads(content)

            if decision.get("tool") == "none":
                return decision.get("message", "I can only help with weather queries.")

            # Execute the tool
            tool_name = decision["tool"]
            arguments = decision.get("arguments", {})

            # Validate tool name
            if tool_name not in tool_names:
                return f"Unknown tool: '{tool_name}'. Available tools: {', '.join(tool_names)}"

            # Add default days for forecast if not specified
            if tool_name == "get_weather_forecast" and "days" not in arguments:
                arguments["days"] = 3

            result = await self._call_mcp_tool(tool_name, arguments)
            
            # Format the result nicely
            return self._format_weather_response(result, tool_name)

        except Exception as e:
            print(f"ERROR in _understand_and_execute: {e}")
            return f"Error processing request: {str(e)}"
    
    def _format_weather_response(self, result: str, tool_name: str) -> str:
        """Format the MCP tool result into a nice response."""
        try:
            data = json.loads(result)
            
            if "error" in data:
                return f"❌ {data['error']}"
            
            if tool_name == "get_current_weather":
                return f"""🌍 Weather in {data.get('city', 'Unknown')}:
🌡️ Temperature: {data.get('temperature_c', 'N/A')}°C
💨 Wind Speed: {data.get('wind_speed_kmh', 'N/A')} km/h
🕐 Last updated: {data.get('timestamp', 'N/A')}"""
            
            elif tool_name == "get_weather_forecast":
                forecast = data.get('forecast', [])
                city = data.get('city', 'Unknown')
                days = data.get('days', 3)
                response = f"📅 {days}-Day Forecast for {city}:\n\n"
                for day in forecast:
                    response += f"📆 {day['date']}: {day['min_temp']}°C - {day['max_temp']}°C\n"
                return response
            
            return result
            
        except Exception as e:
            print(f"Format error: {e}")
            return result
    
    async def process_message(self, message: str, session_id: Optional[str] = None, sender_id: Optional[str] = None) -> str:
        """Process incoming message via A2A protocol."""
        print(f"📨 Weather Agent received: {message[:50]}...")
        
        try:
            # Ensure MCP server is running
            if not self.mcp_initialized:
                await self._start_mcp_server()

            # Use LLM to understand and execute
            response = await self._understand_and_execute(message)
            print(f"📤 Weather Agent responding: {response[:50]}...")
            return response
            
        except Exception as e:
            print(f"ERROR in process_message: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def cleanup(self):
        """Clean up MCP connections."""
        # No need to close MCP client with new API
        if self.mcp_process:
            self.mcp_process.terminate()
            await asyncio.sleep(1)
        self.mcp_initialized = False
    
    async def stop(self):
        """Stop the agent."""
        await self.cleanup()
        await super().stop()
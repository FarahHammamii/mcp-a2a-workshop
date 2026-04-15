"""
MCP Weather Server - Simplified working version.
"""

import asyncio
import json
import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types


class WeatherMCPServer:
    """Simplified MCP Server that works with current library version."""
    
    def __init__(self):
        self.server = Server("weather-mcp-server")
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="get_current_weather",
                    description="Get current weather for a city. Returns temperature in Celsius.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name (e.g., 'London', 'Tokyo')"
                            }
                        },
                        "required": ["city"]
                    }
                ),
                types.Tool(
                    name="get_weather_forecast",
                    description="Get weather forecast for a city.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days (1-5)",
                                "default": 3
                            }
                        },
                        "required": ["city"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Execute tool."""
            if not arguments:
                arguments = {}
            
            if name == "get_current_weather":
                result = await self._get_current_weather(arguments.get("city", ""))
            elif name == "get_weather_forecast":
                result = await self._get_weather_forecast(
                    arguments.get("city", ""), 
                    arguments.get("days", 3)
                )
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [types.TextContent(type="text", text=json.dumps(result))]
    
    async def _get_coordinates(self, city: str):
        """Get city coordinates."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "format": "json"}
            )
            data = resp.json()
            if data.get("results"):
                r = data["results"][0]
                return (r["latitude"], r["longitude"])
        return None
    
    async def _get_current_weather(self, city: str) -> dict:
        """Get current weather."""
        coords = await self._get_coordinates(city)
        if not coords:
            return {"error": f"City not found: {city}"}
        
        lat, lon = coords
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": lat, "longitude": lon, "current_weather": True}
            )
            data = resp.json()
            current = data.get("current_weather", {})
            
            return {
                "city": city,
                "temperature_c": current.get("temperature"),
                "wind_speed_kmh": current.get("windspeed"),
                "timestamp": current.get("time")
            }
    
    async def _get_weather_forecast(self, city: str, days: int) -> dict:
        """Get forecast."""
        coords = await self._get_coordinates(city)
        if not coords:
            return {"error": f"City not found: {city}"}
        
        lat, lon = coords
        days = min(max(days, 1), 5)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": ["temperature_2m_max", "temperature_2m_min"],
                    "forecast_days": days
                }
            )
            data = resp.json()
            daily = data.get("daily", {})
            
            forecast = []
            for i in range(len(daily.get("time", []))):
                forecast.append({
                    "date": daily["time"][i],
                    "max_temp": daily["temperature_2m_max"][i],
                    "min_temp": daily["temperature_2m_min"][i]
                })
            
            return {"city": city, "forecast": forecast, "days": days}
    
    async def run(self):
        """Run server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="weather-mcp-server",
                    server_version="1.0.0",
                    capabilities=types.ServerCapabilities(tools=types.ToolsCapability())
                )
            )


if __name__ == "__main__":
    asyncio.run(WeatherMCPServer().run())
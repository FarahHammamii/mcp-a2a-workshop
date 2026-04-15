"""
Base A2A Agent - Implements common A2A protocol functionality.
"""

import asyncio
import sys
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from sse_starlette.sse import EventSourceResponse


class A2AMessage(BaseModel):
    """A2A protocol message format."""
    message: str
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    sender_id: Optional[str] = None


class A2AResponse(BaseModel):
    """A2A protocol response format."""
    response: str
    session_id: str
    task_id: str
    status: str
    sender_id: str


class BaseA2AAgent(ABC):
    """
    Base class for A2A-compliant agents.
    Implements the core A2A protocol endpoints.
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0", port: int = 8000):
        self.name = name
        self.description = description
        self.version = version
        self.port = port
        self.agent_id = f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        
        # Create FastAPI app
        self.app = FastAPI(
            title=name,
            description=description,
            version=version
        )
        
        self._setup_routes()
        self._setup_cors()
    
    def _setup_cors(self):
        """Setup CORS for the agent."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup A2A protocol routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "endpoints": {
                    "agent_card": "/.well-known/agent-card.json",
                    "send_message": "/v1/message:send",
                    "stream_message": "/v1/message:stream",
                    "health": "/health"
                }
            }
        
        @self.app.get("/.well-known/agent-card.json")
        async def agent_card():
            """A2A agent discovery endpoint."""
            return {
                "id": self.agent_id,
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "capabilities": self.get_capabilities(),
                "endpoints": {
                    "message": f"http://localhost:{self.port}/v1/message:send",
                    "stream": f"http://localhost:{self.port}/v1/message:stream"
                }
            }
        
        @self.app.post("/v1/message:send")
        async def send_message(request: A2AMessage):
            """A2A message sending endpoint."""
            try:
                response_text = await self.process_message(
                    request.message,
                    session_id=request.session_id,
                    sender_id=request.sender_id
                )
                
                return A2AResponse(
                    response=response_text,
                    session_id=request.session_id or "default",
                    task_id=request.task_id or str(uuid.uuid4()),
                    status="completed",
                    sender_id=self.agent_id
                )
            except Exception as e:
                print(f"ERROR in /v1/message:send: {e}", file=sys.stderr)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/v1/message:stream")
        async def stream_message(request: A2AMessage):
            """A2A streaming endpoint."""
            async def event_generator():
                async for chunk in self.stream_message(
                    request.message,
                    session_id=request.session_id,
                    sender_id=request.sender_id
                ):
                    yield {
                        "event": "message",
                        "data": chunk
                    }
                yield {
                    "event": "done",
                    "data": "Stream completed"
                }
            
            return EventSourceResponse(event_generator())
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "agent": self.name, "agent_id": self.agent_id}
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for A2A discovery."""
        pass
    
    @abstractmethod
    async def process_message(self, message: str, session_id: Optional[str] = None, sender_id: Optional[str] = None) -> str:
        """Process a message and return response."""
        pass
    
    async def stream_message(self, message: str, session_id: Optional[str] = None, sender_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Stream a response (default implementation yields full response)."""
        response = await self.process_message(message, session_id, sender_id)
        yield response
    
    async def run(self):
        """Run the agent server asynchronously."""
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        try:
            await server.serve()
        except asyncio.CancelledError:
            server.should_exit = True
            raise
"""
WebSocket Manager for Real-time Agent Logs
Ghost Mode - Live streaming of agent activity
"""

from fastapi import WebSocket
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time log streaming"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._log_buffer: List[Dict[str, Any]] = []
        self._max_buffer = 100
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send recent logs to new connection
        if self._log_buffer:
            await websocket.send_json({
                "type": "history",
                "logs": self._log_buffer[-50:]
            })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_log(self, log_entry: Dict[str, Any]):
        """Broadcast log entry to all connected clients"""
        # Add to buffer
        self._log_buffer.append(log_entry)
        if len(self._log_buffer) > self._max_buffer:
            self._log_buffer = self._log_buffer[-self._max_buffer:]
        
        # Broadcast to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "log",
                    "data": log_entry
                })
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_processing_start(self, filename: str):
        """Notify clients that processing has started"""
        await self._broadcast({
            "type": "processing_start",
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_processing_complete(self, result: Dict[str, Any]):
        """Notify clients that processing is complete"""
        await self._broadcast({
            "type": "processing_complete",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _broadcast(self, message: Dict[str, Any]):
        """Internal broadcast helper"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


# Global manager instance
ws_manager = ConnectionManager()


def get_ws_manager() -> ConnectionManager:
    """Get the WebSocket manager instance"""
    return ws_manager

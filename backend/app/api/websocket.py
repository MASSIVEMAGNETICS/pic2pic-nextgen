"""
WebSocket Routes
================
Real-time bidirectional communication for live preview streaming
and shard activation visualization.
"""
import asyncio
import json
import logging
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.engine import (
    HolographicReconstructionEngine,
    ReconstructionMode,
    ReconstructionProgress,
)
from ..core.self_healing import HealthStatus, SelfHealingWatchdog

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for broadcasting updates."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.job_subscriptions: dict[str, set[str]] = {}  # job_id -> connection_ids

    async def connect(self, websocket: WebSocket) -> str:
        """Accept connection and return connection ID."""
        await websocket.accept()
        connection_id = str(uuid4())
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")
        return connection_id

    def disconnect(self, connection_id: str) -> None:
        """Remove connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Remove from all job subscriptions
            for job_subs in self.job_subscriptions.values():
                job_subs.discard(connection_id)
            logger.info(f"WebSocket disconnected: {connection_id}")

    def subscribe_to_job(self, connection_id: str, job_id: str) -> None:
        """Subscribe connection to job updates."""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(connection_id)

    async def send_personal(self, connection_id: str, message: dict) -> None:
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_json(message)

    async def broadcast_to_job(self, job_id: str, message: dict) -> None:
        """Broadcast message to all connections subscribed to a job."""
        if job_id in self.job_subscriptions:
            for conn_id in self.job_subscriptions[job_id]:
                if conn_id in self.active_connections:
                    try:
                        await self.active_connections[conn_id].send_json(message)
                    except Exception as e:
                        logger.warning(f"Failed to send to {conn_id}: {e}")

    async def broadcast_all(self, message: dict) -> None:
        """Broadcast to all connected clients."""
        for conn_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to {conn_id}: {e}")


# Global connection manager
manager = ConnectionManager()

# Shared resources
_watchdog: SelfHealingWatchdog | None = None
_engine: HolographicReconstructionEngine | None = None


def get_watchdog() -> SelfHealingWatchdog:
    """Get or create watchdog instance."""
    global _watchdog
    if _watchdog is None:
        _watchdog = SelfHealingWatchdog()
    return _watchdog


def get_engine() -> HolographicReconstructionEngine:
    """Get or create engine instance."""
    global _engine
    if _engine is None:
        _engine = HolographicReconstructionEngine()
    return _engine


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time communication.

    Message types:
    - subscribe: Subscribe to job updates
    - process: Start image processing with live preview
    - health: Get current system health
    - dev_params: Get/set dev parameters (dev mode)
    """
    connection_id = await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal(
            connection_id,
            {
                "type": "connected",
                "connection_id": connection_id,
                "message": "Connected to pic2pic-nextgen",
            },
        )

        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            if msg_type == "subscribe":
                # Subscribe to job updates
                job_id = message.get("job_id")
                if job_id:
                    manager.subscribe_to_job(connection_id, job_id)
                    await manager.send_personal(
                        connection_id,
                        {"type": "subscribed", "job_id": job_id},
                    )

            elif msg_type == "process":
                # Start processing with live preview
                await handle_process_request(connection_id, message)

            elif msg_type == "health":
                # Get system health
                await handle_health_request(connection_id)

            elif msg_type == "dev_params":
                # Dev mode: get/set parameters
                await handle_dev_params(connection_id, message)

            elif msg_type == "ping":
                # Keepalive
                await manager.send_personal(connection_id, {"type": "pong"})

            else:
                await manager.send_personal(
                    connection_id,
                    {"type": "error", "message": f"Unknown message type: {msg_type}"},
                )

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except json.JSONDecodeError:
        await manager.send_personal(
            connection_id,
            {"type": "error", "message": "Invalid JSON"},
        )
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)


async def handle_process_request(connection_id: str, message: dict) -> None:
    """Handle image processing request with live preview streaming."""
    import base64

    image_data = message.get("image_data")  # Base64 encoded
    mode_str = message.get("mode", "enhance")

    if not image_data:
        await manager.send_personal(
            connection_id,
            {"type": "error", "message": "No image data provided"},
        )
        return

    try:
        mode = ReconstructionMode(mode_str)
    except ValueError:
        mode = ReconstructionMode.ENHANCE

    # Decode image
    try:
        image_bytes = base64.b64decode(image_data)
    except Exception:
        await manager.send_personal(
            connection_id,
            {"type": "error", "message": "Invalid base64 image data"},
        )
        return

    job_id = str(uuid4())

    # Notify processing started
    await manager.send_personal(
        connection_id,
        {
            "type": "processing_started",
            "job_id": job_id,
            "mode": mode.value,
        },
    )

    # Subscribe to this job
    manager.subscribe_to_job(connection_id, job_id)

    # Get engine and set up progress callback
    engine = get_engine()

    async def progress_callback(progress: ReconstructionProgress):
        """Stream progress updates to WebSocket."""
        shard_data = [
            {
                "shard_id": s.shard_id,
                "scale": s.scale,
                "activation": s.activation,
                "coordinates": s.coordinates,
            }
            for s in progress.shard_activations
        ]

        await manager.broadcast_to_job(
            job_id,
            {
                "type": "progress",
                "job_id": job_id,
                "step": progress.step,
                "total_steps": progress.total_steps,
                "progress_percent": progress.progress_percent,
                "current_scale": progress.current_scale,
                "active_shards": progress.active_shards,
                "shard_activations": shard_data,
            },
        )

    # Wrap sync callback for async
    def sync_progress_callback(progress: ReconstructionProgress):
        asyncio.create_task(progress_callback(progress))

    engine.set_progress_callback(sync_progress_callback)

    # Process image
    try:
        result = await engine.reconstruct(image_bytes, mode)

        # Send completion
        await manager.broadcast_to_job(
            job_id,
            {
                "type": "completed",
                "job_id": job_id,
                "result": base64.b64encode(result).decode(),
            },
        )
    except Exception as e:
        logger.error(f"Processing error: {e}")
        watchdog = get_watchdog()
        watchdog.handle_error(e)

        await manager.broadcast_to_job(
            job_id,
            {
                "type": "error",
                "job_id": job_id,
                "message": str(e),
            },
        )


async def handle_health_request(connection_id: str) -> None:
    """Handle health status request."""
    watchdog = get_watchdog()
    health = await watchdog.check_health()

    await manager.send_personal(
        connection_id,
        {
            "type": "health",
            "status": health.status.value,
            "device_mode": health.device_mode.value,
            "memory_usage_mb": health.memory_usage_mb,
            "cpu_temp_c": health.cpu_temp_c,
            "last_checkpoint": health.last_checkpoint,
            "consecutive_failures": health.consecutive_failures,
            "message": health.message,
        },
    )


async def handle_dev_params(connection_id: str, message: dict) -> None:
    """Handle dev parameter get/set requests."""
    action = message.get("action", "get")
    engine = get_engine()

    if action == "get":
        params = engine.parameters
        await manager.send_personal(
            connection_id,
            {
                "type": "dev_params",
                "action": "get",
                "params": {
                    "tau_scale_1": params.tau_scale_1,
                    "tau_scale_2": params.tau_scale_2,
                    "tau_scale_3": params.tau_scale_3,
                    "tau_scale_4": params.tau_scale_4,
                    "cleanup_k_top": params.cleanup_k_top,
                    "binding_temperature": params.binding_temperature,
                    "binding_strength": params.binding_strength,
                    "cosine_threshold": params.cosine_threshold,
                },
            },
        )
    elif action == "set":
        params_update = message.get("params", {})
        for key, value in params_update.items():
            if hasattr(engine.parameters, key):
                setattr(engine.parameters, key, value)

        await manager.send_personal(
            connection_id,
            {
                "type": "dev_params",
                "action": "set",
                "status": "updated",
            },
        )

"""
Self-Healing System
==================
Watchdog, checkpoint recovery, and graceful degradation for production stability.
"""
import asyncio
import logging
import os
import signal
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RECOVERING = "recovering"


class DeviceMode(str, Enum):
    """Compute device mode."""

    CUDA = "cuda"
    CPU = "cpu"
    MPS = "mps"  # Apple Silicon


@dataclass
class SystemHealth:
    """Current system health state."""

    status: HealthStatus
    device_mode: DeviceMode
    memory_usage_mb: float
    cpu_temp_c: float | None
    last_checkpoint: str | None
    consecutive_failures: int
    message: str


class CheckpointManager:
    """
    Manages checkpoints for atomic recovery.
    Saves state every N batches with atomic swap.
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_checkpoint: Path | None = None
        self.checkpoint_count = 0

    def save_checkpoint(self, state: dict, name: str = "auto") -> Path:
        """
        Save checkpoint with atomic swap.
        Creates temp file, writes, then atomically renames.
        """
        import json

        timestamp = int(time.time())
        checkpoint_name = f"{name}_{timestamp}_{self.checkpoint_count}.json"
        final_path = self.checkpoint_dir / checkpoint_name

        # Atomic write: write to temp, then rename
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.checkpoint_dir,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(state, tmp)
            tmp_path = tmp.name

        # Atomic rename
        os.rename(tmp_path, final_path)

        self.current_checkpoint = final_path
        self.checkpoint_count += 1
        logger.info(f"Saved checkpoint: {final_path}")

        # Cleanup old checkpoints (keep last 5)
        self._cleanup_old_checkpoints(keep=5)

        return final_path

    def load_latest_checkpoint(self) -> dict | None:
        """Load the most recent valid checkpoint."""
        import json

        checkpoints = sorted(
            self.checkpoint_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for checkpoint in checkpoints:
            try:
                with open(checkpoint, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded checkpoint: {checkpoint}")
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load checkpoint {checkpoint}: {e}")
                continue

        return None

    def _cleanup_old_checkpoints(self, keep: int = 5) -> None:
        """Remove old checkpoints, keeping the most recent N."""
        checkpoints = sorted(
            self.checkpoint_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for checkpoint in checkpoints[keep:]:
            try:
                checkpoint.unlink()
                logger.debug(f"Removed old checkpoint: {checkpoint}")
            except OSError:
                pass


class GracefulDegradation:
    """
    Handles graceful fallback from GPU to CPU on failures.
    """

    def __init__(self):
        self.current_device = DeviceMode.CPU
        self.cuda_available = False
        self.cuda_failure_count = 0
        self.max_cuda_failures = 3
        self._check_cuda_availability()

    def _check_cuda_availability(self) -> None:
        """Check if CUDA is available."""
        try:
            import torch

            self.cuda_available = torch.cuda.is_available()
            if self.cuda_available:
                self.current_device = DeviceMode.CUDA
                logger.info("CUDA available, using GPU")
        except ImportError:
            logger.info("PyTorch not installed, using CPU mode")
            self.cuda_available = False

    def handle_cuda_error(self, error: Exception) -> DeviceMode:
        """
        Handle CUDA error by falling back to CPU.
        Returns the new device mode.
        """
        self.cuda_failure_count += 1
        logger.warning(f"CUDA error ({self.cuda_failure_count}): {error}")

        if self.cuda_failure_count >= self.max_cuda_failures:
            logger.warning("Max CUDA failures reached, falling back to CPU")
            self.current_device = DeviceMode.CPU
            self._flush_gpu_memory()

        return self.current_device

    def _flush_gpu_memory(self) -> None:
        """Flush GPU memory to recover from OOM."""
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                logger.info("GPU memory flushed")
        except (ImportError, RuntimeError) as e:
            logger.warning(f"Failed to flush GPU memory: {e}")

    def get_device(self) -> str:
        """Get current device string for torch."""
        return self.current_device.value

    def reset_cuda(self) -> bool:
        """
        Attempt to reset CUDA and return to GPU mode.
        Returns True if successful.
        """
        if not self.cuda_available:
            return False

        self._flush_gpu_memory()
        try:
            import torch

            # Test CUDA with small allocation
            test_tensor = torch.zeros(1, device="cuda")
            del test_tensor
            torch.cuda.empty_cache()

            self.current_device = DeviceMode.CUDA
            self.cuda_failure_count = 0
            logger.info("Successfully reset to CUDA mode")
            return True
        except (ImportError, RuntimeError) as e:
            logger.warning(f"CUDA reset failed: {e}")
            return False


class SelfHealingWatchdog:
    """
    Watchdog system for auto-restart and health monitoring.
    """

    def __init__(
        self,
        restart_delay: float = 3.0,
        health_check_interval: float = 30.0,
        max_memory_mb: float = 4096.0,
        cpu_temp_threshold: float = 85.0,
    ):
        self.restart_delay = restart_delay
        self.health_check_interval = health_check_interval
        self.max_memory_mb = max_memory_mb
        self.cpu_temp_threshold = cpu_temp_threshold
        self.checkpoint_manager = CheckpointManager()
        self.degradation = GracefulDegradation()
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self.is_running = False
        self._health_task: asyncio.Task | None = None
        self._on_unhealthy: Callable[[], None] | None = None

    def set_unhealthy_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for when system becomes unhealthy."""
        self._on_unhealthy = callback

    async def start(self) -> None:
        """Start the watchdog health monitoring."""
        self.is_running = True
        self._health_task = asyncio.create_task(self._health_check_loop())
        logger.info("Self-healing watchdog started")

    async def stop(self) -> None:
        """Stop the watchdog."""
        self.is_running = False
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        logger.info("Self-healing watchdog stopped")

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while self.is_running:
            try:
                health = await self.check_health()

                if health.status == HealthStatus.UNHEALTHY:
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.max_consecutive_failures:
                        logger.critical("Max consecutive failures reached")
                        if self._on_unhealthy:
                            self._on_unhealthy()
                else:
                    self.consecutive_failures = 0

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def check_health(self) -> SystemHealth:
        """
        Perform comprehensive health check.
        Returns current system health state.
        """
        import psutil

        # Get memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)

        # Try to get CPU temperature (platform-dependent)
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        cpu_temp = entries[0].current
                        break
        except (AttributeError, KeyError):
            pass

        # Determine status
        status = HealthStatus.HEALTHY
        message = "System operating normally"

        if memory_mb > self.max_memory_mb:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {memory_mb:.1f}MB"

        if cpu_temp and cpu_temp > self.cpu_temp_threshold:
            status = HealthStatus.DEGRADED
            message = f"High CPU temperature: {cpu_temp:.1f}°C"

        if self.degradation.current_device == DeviceMode.CPU and self.degradation.cuda_available:
            status = HealthStatus.DEGRADED
            message = "Running in CPU fallback mode"

        last_checkpoint = None
        if self.checkpoint_manager.current_checkpoint:
            last_checkpoint = str(self.checkpoint_manager.current_checkpoint)

        return SystemHealth(
            status=status,
            device_mode=self.degradation.current_device,
            memory_usage_mb=memory_mb,
            cpu_temp_c=cpu_temp,
            last_checkpoint=last_checkpoint,
            consecutive_failures=self.consecutive_failures,
            message=message,
        )

    def save_checkpoint(self, state: dict) -> Path:
        """Save a checkpoint through the manager."""
        return self.checkpoint_manager.save_checkpoint(state)

    def recover_from_checkpoint(self) -> dict | None:
        """Attempt to recover from the latest checkpoint."""
        return self.checkpoint_manager.load_latest_checkpoint()

    def handle_error(self, error: Exception) -> None:
        """
        Handle an error with appropriate recovery strategy.
        """
        error_type = type(error).__name__

        # Handle CUDA OOM specifically
        if "OutOfMemoryError" in error_type or "CUDA" in str(error):
            self.degradation.handle_cuda_error(error)
            return

        # Handle other recoverable errors
        if isinstance(error, (OSError, IOError)):
            logger.warning(f"IO error, attempting recovery: {error}")
            return

        # Log unhandled errors
        logger.error(f"Unhandled error in self-healing: {error}")
        self.consecutive_failures += 1

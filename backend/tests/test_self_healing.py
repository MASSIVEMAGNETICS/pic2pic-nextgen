"""
Tests for the self-healing system.
"""
import pytest
import tempfile
from pathlib import Path

from app.core.self_healing import (
    CheckpointManager,
    GracefulDegradation,
    SelfHealingWatchdog,
    DeviceMode,
    HealthStatus,
)


class TestCheckpointManager:
    """Test checkpoint management."""

    def test_create_manager(self):
        """Test creating checkpoint manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            assert manager.checkpoint_dir.exists()
            assert manager.current_checkpoint is None

    def test_save_checkpoint(self):
        """Test saving a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            state = {"model_state": [1, 2, 3], "epoch": 5}

            path = manager.save_checkpoint(state, name="test")

            assert path.exists()
            assert manager.current_checkpoint == path

    def test_load_latest_checkpoint(self):
        """Test loading the latest checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)

            # Save multiple checkpoints
            manager.save_checkpoint({"epoch": 1}, name="test")
            manager.save_checkpoint({"epoch": 2}, name="test")
            manager.save_checkpoint({"epoch": 3}, name="test")

            # Load latest
            loaded = manager.load_latest_checkpoint()
            assert loaded is not None
            assert loaded["epoch"] == 3

    def test_cleanup_old_checkpoints(self):
        """Test cleanup of old checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)

            # Save many checkpoints
            for i in range(10):
                manager.save_checkpoint({"epoch": i}, name="test")

            # Should only keep last 5
            checkpoints = list(Path(tmpdir).glob("*.json"))
            assert len(checkpoints) == 5

    def test_load_no_checkpoints(self):
        """Test loading when no checkpoints exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            loaded = manager.load_latest_checkpoint()
            assert loaded is None


class TestGracefulDegradation:
    """Test graceful degradation handling."""

    def test_create_degradation(self):
        """Test creating degradation handler."""
        degradation = GracefulDegradation()
        # Should default to CPU if CUDA not available
        assert degradation.current_device in [DeviceMode.CUDA, DeviceMode.CPU]

    def test_get_device(self):
        """Test getting current device string."""
        degradation = GracefulDegradation()
        device = degradation.get_device()
        assert device in ["cuda", "cpu", "mps"]

    def test_handle_cuda_error(self):
        """Test handling CUDA errors."""
        degradation = GracefulDegradation()
        degradation.cuda_available = True  # Pretend CUDA was available

        # Simulate multiple CUDA errors
        for _ in range(3):
            degradation.handle_cuda_error(RuntimeError("CUDA OOM"))

        # After 3 failures, should fall back to CPU
        assert degradation.current_device == DeviceMode.CPU

    def test_cuda_failure_count(self):
        """Test CUDA failure counting."""
        degradation = GracefulDegradation()
        initial_count = degradation.cuda_failure_count

        degradation.handle_cuda_error(RuntimeError("test"))
        assert degradation.cuda_failure_count == initial_count + 1


class TestSelfHealingWatchdog:
    """Test the self-healing watchdog."""

    def test_create_watchdog(self):
        """Test creating watchdog."""
        watchdog = SelfHealingWatchdog()
        assert watchdog.restart_delay == 3.0
        assert watchdog.consecutive_failures == 0
        assert not watchdog.is_running

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping watchdog."""
        watchdog = SelfHealingWatchdog(health_check_interval=0.1)

        await watchdog.start()
        assert watchdog.is_running

        await watchdog.stop()
        assert not watchdog.is_running

    @pytest.mark.asyncio
    async def test_check_health(self):
        """Test health check."""
        watchdog = SelfHealingWatchdog()
        health = await watchdog.check_health()

        assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert health.memory_usage_mb > 0
        assert health.device_mode in [DeviceMode.CUDA, DeviceMode.CPU, DeviceMode.MPS]

    def test_save_checkpoint(self):
        """Test checkpoint saving through watchdog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watchdog = SelfHealingWatchdog()
            watchdog.checkpoint_manager = CheckpointManager(checkpoint_dir=tmpdir)

            path = watchdog.save_checkpoint({"test": "data"})
            assert path.exists()

    def test_recover_from_checkpoint(self):
        """Test checkpoint recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watchdog = SelfHealingWatchdog()
            watchdog.checkpoint_manager = CheckpointManager(checkpoint_dir=tmpdir)

            # Save and recover
            watchdog.save_checkpoint({"test": "data", "value": 42})
            recovered = watchdog.recover_from_checkpoint()

            assert recovered is not None
            assert recovered["value"] == 42

    def test_handle_error(self):
        """Test error handling."""
        watchdog = SelfHealingWatchdog()
        initial_failures = watchdog.consecutive_failures

        # Handle a generic error
        watchdog.handle_error(ValueError("test error"))

        # Should increment failure count
        assert watchdog.consecutive_failures == initial_failures + 1

    def test_handle_cuda_oom(self):
        """Test handling CUDA OOM errors."""
        watchdog = SelfHealingWatchdog()

        # Simulate CUDA OOM
        class MockCudaOOM(Exception):
            pass

        MockCudaOOM.__name__ = "OutOfMemoryError"

        watchdog.handle_error(MockCudaOOM("CUDA out of memory"))

        # Should be handled gracefully (no crash)
        assert True

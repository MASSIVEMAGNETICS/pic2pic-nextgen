"""
Tests for the holographic reconstruction engine.
"""
import pytest
from pathlib import Path
import tempfile

from app.core.engine import (
    HolographicParameters,
    HolographicMemoryBank,
    HolographicReconstructionEngine,
    ReconstructionMode,
    ReconstructionProgress,
)


class TestHolographicParameters:
    """Test parameter configuration."""

    def test_default_parameters(self):
        """Test default parameter values."""
        params = HolographicParameters()
        assert params.tau_scale_1 == 0.1
        assert params.tau_scale_2 == 0.2
        assert params.tau_scale_3 == 0.3
        assert params.tau_scale_4 == 0.4
        assert params.cleanup_k_top == 50
        assert params.binding_temperature == 1.0
        assert params.binding_strength == 0.8
        assert params.cosine_threshold == 0.92

    def test_from_preset_enhance(self):
        """Test Enhance preset parameters."""
        params = HolographicParameters.from_preset(ReconstructionMode.ENHANCE)
        assert params.tau_scale_1 == 0.15
        assert params.tau_scale_2 == 0.25
        assert params.binding_strength == 0.9

    def test_from_preset_stylize(self):
        """Test Stylize preset parameters."""
        params = HolographicParameters.from_preset(ReconstructionMode.STYLIZE)
        assert params.binding_temperature == 1.5
        assert params.tau_scale_3 == 0.4

    def test_from_preset_de_old_photo(self):
        """Test De-old-photo preset parameters."""
        params = HolographicParameters.from_preset(ReconstructionMode.DE_OLD_PHOTO)
        assert params.cleanup_k_top == 30
        assert params.binding_strength == 0.95

    def test_from_preset_make_anime(self):
        """Test Make-anime preset parameters."""
        params = HolographicParameters.from_preset(ReconstructionMode.MAKE_ANIME)
        assert params.binding_temperature == 2.0
        assert params.tau_scale_3 == 0.45


class TestHolographicMemoryBank:
    """Test memory bank operations."""

    def test_create_memory_bank(self):
        """Test creating a memory bank."""
        bank = HolographicMemoryBank(name="test")
        assert bank.name == "test"
        assert len(bank.shards) == 0
        assert bank.scale_count == 4

    def test_add_shard(self):
        """Test adding shards to memory bank."""
        bank = HolographicMemoryBank()
        bank.add_shard(1, {"activation": 0.95, "data": [1, 2, 3]})
        bank.add_shard(2, {"activation": 0.85, "data": [4, 5, 6]})
        assert len(bank.shards) == 2
        assert bank.get_shard(1)["activation"] == 0.95

    def test_cleanup_low_activation_shards(self):
        """Test cleaning up low activation shards."""
        bank = HolographicMemoryBank()
        bank.add_shard(1, {"activation": 0.95})
        bank.add_shard(2, {"activation": 0.85})
        bank.add_shard(3, {"activation": 0.99})

        removed = bank.cleanup_low_activation_shards(threshold=0.90)
        assert removed == 1
        assert len(bank.shards) == 2
        assert bank.get_shard(2) is None

    def test_save_and_load(self):
        """Test saving and loading memory bank."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.holo"

            # Create and save
            bank = HolographicMemoryBank(name="test_bank")
            bank.add_shard(1, {"activation": 0.95})
            bank.save(path)

            # Load and verify
            loaded = HolographicMemoryBank.load(path)
            assert loaded.name == "test_bank"
            assert len(loaded.shards) == 1


class TestHolographicReconstructionEngine:
    """Test the reconstruction engine."""

    def test_create_engine(self):
        """Test creating an engine instance."""
        engine = HolographicReconstructionEngine()
        assert engine.memory_bank is not None
        assert engine.parameters is not None
        assert engine.operation_count == 0

    def test_progress_callback(self):
        """Test progress callback mechanism."""
        engine = HolographicReconstructionEngine()
        progress_updates = []

        def callback(progress: ReconstructionProgress):
            progress_updates.append(progress)

        engine.set_progress_callback(callback)
        engine._emit_progress(ReconstructionProgress(
            step=1,
            total_steps=10,
            current_scale=1,
            active_shards=5
        ))

        assert len(progress_updates) == 1
        assert progress_updates[0].progress_percent == 10.0

    def test_integrity_check_interval(self):
        """Test integrity check scheduling."""
        engine = HolographicReconstructionEngine()

        # Should not run at start
        assert not engine.should_run_integrity_check(interval=100)

        # Simulate operations
        engine.operation_count = 100
        assert engine.should_run_integrity_check(interval=100)

        engine.operation_count = 150
        assert not engine.should_run_integrity_check(interval=100)

        engine.operation_count = 200
        assert engine.should_run_integrity_check(interval=100)

    @pytest.mark.asyncio
    async def test_reconstruct_basic(self):
        """Test basic reconstruction."""
        engine = HolographicReconstructionEngine()
        # Use small cleanup_k_top for faster test
        engine.parameters.cleanup_k_top = 5

        input_data = b"test_image_data"
        result = await engine.reconstruct(input_data, ReconstructionMode.ENHANCE)

        assert result == input_data  # Placeholder returns same data
        assert engine.operation_count > 0


class TestReconstructionProgress:
    """Test progress reporting."""

    def test_progress_percent_zero(self):
        """Test progress with zero total steps."""
        progress = ReconstructionProgress(
            step=0,
            total_steps=0,
            current_scale=1,
            active_shards=0
        )
        assert progress.progress_percent == 0.0

    def test_progress_percent_calculation(self):
        """Test progress percentage calculation."""
        progress = ReconstructionProgress(
            step=50,
            total_steps=100,
            current_scale=2,
            active_shards=10
        )
        assert progress.progress_percent == 50.0

    def test_progress_percent_complete(self):
        """Test 100% progress."""
        progress = ReconstructionProgress(
            step=100,
            total_steps=100,
            current_scale=4,
            active_shards=25
        )
        assert progress.progress_percent == 100.0

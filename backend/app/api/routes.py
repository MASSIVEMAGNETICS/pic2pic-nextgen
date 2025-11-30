"""
REST API Routes
===============
HTTP endpoints for image upload, presets, and batch processing.
"""
import base64
import logging
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from ..config import settings, DeploymentTier
from ..core.engine import (
    HolographicMemoryBank,
    HolographicParameters,
    HolographicReconstructionEngine,
    ReconstructionMode,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    deployment_tier: str


class PresetInfo(BaseModel):
    """Preset information."""

    name: str
    mode: str
    description: str


class ProcessRequest(BaseModel):
    """Image processing request."""

    mode: ReconstructionMode = ReconstructionMode.ENHANCE
    strength: float = 1.0


class ProcessResponse(BaseModel):
    """Image processing response."""

    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status response."""

    job_id: str
    status: str
    progress: float
    result_url: str | None = None


class DevParametersRequest(BaseModel):
    """Dev mode parameter update request."""

    tau_scale_1: float | None = None
    tau_scale_2: float | None = None
    tau_scale_3: float | None = None
    tau_scale_4: float | None = None
    cleanup_k_top: int | None = None
    binding_temperature: float | None = None
    binding_strength: float | None = None
    cosine_threshold: float | None = None


class MemoryBankInfo(BaseModel):
    """Memory bank information."""

    name: str
    shard_count: int
    scale_count: int
    version: str


# ============================================================================
# In-memory stores (would be Redis/DB in production)
# ============================================================================

# Job tracking
jobs: dict[str, dict] = {}

# Current engine instance
_engine: HolographicReconstructionEngine | None = None


def get_engine() -> HolographicReconstructionEngine:
    """Get or create the reconstruction engine."""
    global _engine
    if _engine is None:
        _engine = HolographicReconstructionEngine()
    return _engine


# ============================================================================
# Health & Info Endpoints
# ============================================================================


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        deployment_tier=settings.deployment_tier.value,
    )


@router.get("/presets", response_model=list[PresetInfo])
async def list_presets() -> list[PresetInfo]:
    """List available reconstruction presets."""
    return [
        PresetInfo(
            name="Enhance",
            mode=ReconstructionMode.ENHANCE.value,
            description="Improve image quality and clarity",
        ),
        PresetInfo(
            name="Stylize",
            mode=ReconstructionMode.STYLIZE.value,
            description="Apply artistic style transformation",
        ),
        PresetInfo(
            name="De-old Photo",
            mode=ReconstructionMode.DE_OLD_PHOTO.value,
            description="Restore and enhance old photographs",
        ),
        PresetInfo(
            name="Make Anime",
            mode=ReconstructionMode.MAKE_ANIME.value,
            description="Transform to anime/illustration style",
        ),
    ]


# ============================================================================
# Image Processing Endpoints
# ============================================================================


@router.post("/upload", response_model=ProcessResponse)
async def upload_image(
    file: Annotated[UploadFile, File(description="Image file to process")],
    mode: ReconstructionMode = ReconstructionMode.ENHANCE,
) -> ProcessResponse:
    """
    Upload an image for processing.
    Returns a job ID for tracking progress.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Create job
    job_id = str(uuid4())
    content = await file.read()

    # Store job info
    jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "mode": mode.value,
        "input_data": content,
        "result_data": None,
    }

    logger.info(f"Created job {job_id} for {mode.value} processing")

    return ProcessResponse(
        job_id=job_id,
        status="queued",
        message=f"Image queued for {mode.value} processing",
    )


@router.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get the status of a processing job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    result_url = f"/api/v1/result/{job_id}" if job["status"] == "completed" else None

    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result_url=result_url,
    )


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """Get the result of a completed job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job["result_data"]:
        raise HTTPException(status_code=500, detail="Result data not available")

    # Return base64 encoded result for simplicity
    return {
        "job_id": job_id,
        "result": base64.b64encode(job["result_data"]).decode(),
    }


# ============================================================================
# Batch Processing Endpoints
# ============================================================================


@router.post("/batch")
async def start_batch(
    files: list[UploadFile],
    mode: ReconstructionMode = ReconstructionMode.ENHANCE,
):
    """
    Start batch processing of multiple images.
    Returns a batch ID for tracking overall progress.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    batch_id = str(uuid4())
    job_ids = []

    for file in files:
        if file.content_type and file.content_type.startswith("image/"):
            job_id = str(uuid4())
            content = await file.read()
            jobs[job_id] = {
                "status": "queued",
                "progress": 0.0,
                "mode": mode.value,
                "input_data": content,
                "result_data": None,
                "batch_id": batch_id,
            }
            job_ids.append(job_id)

    logger.info(f"Created batch {batch_id} with {len(job_ids)} jobs")

    return {
        "batch_id": batch_id,
        "job_count": len(job_ids),
        "job_ids": job_ids,
        "status": "queued",
    }


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of a batch processing job."""
    batch_jobs = [j for j in jobs.values() if j.get("batch_id") == batch_id]

    if not batch_jobs:
        raise HTTPException(status_code=404, detail="Batch not found")

    completed = sum(1 for j in batch_jobs if j["status"] == "completed")
    total_progress = sum(j["progress"] for j in batch_jobs) / len(batch_jobs)

    status = "processing"
    if completed == len(batch_jobs):
        status = "completed"
    elif all(j["status"] == "queued" for j in batch_jobs):
        status = "queued"

    return {
        "batch_id": batch_id,
        "status": status,
        "total_jobs": len(batch_jobs),
        "completed_jobs": completed,
        "progress": total_progress,
    }


# ============================================================================
# Memory Bank Endpoints
# ============================================================================


@router.get("/memory-banks", response_model=list[MemoryBankInfo])
async def list_memory_banks() -> list[MemoryBankInfo]:
    """List available memory banks (.holo files)."""
    presets_dir = Path(settings.holo_presets_dir)
    if not presets_dir.exists():
        return []

    banks = []
    for holo_file in presets_dir.glob("*.holo"):
        try:
            bank = HolographicMemoryBank.load(holo_file)
            banks.append(
                MemoryBankInfo(
                    name=bank.name,
                    shard_count=len(bank.shards),
                    scale_count=bank.scale_count,
                    version=bank.version,
                )
            )
        except Exception as e:
            logger.warning(f"Failed to load memory bank {holo_file}: {e}")

    return banks


@router.post("/memory-banks/{name}/save")
async def save_memory_bank(name: str):
    """Save current memory bank to a .holo file."""
    engine = get_engine()
    presets_dir = Path(settings.holo_presets_dir)
    presets_dir.mkdir(parents=True, exist_ok=True)

    engine.memory_bank.name = name
    save_path = presets_dir / f"{name}.holo"
    engine.memory_bank.save(save_path)

    return {"status": "saved", "path": str(save_path)}


@router.post("/memory-banks/{name}/load")
async def load_memory_bank(name: str):
    """Load a memory bank from a .holo file."""
    presets_dir = Path(settings.holo_presets_dir)
    load_path = presets_dir / f"{name}.holo"

    if not load_path.exists():
        raise HTTPException(status_code=404, detail="Memory bank not found")

    engine = get_engine()
    engine.memory_bank = HolographicMemoryBank.load(load_path)

    return {
        "status": "loaded",
        "name": engine.memory_bank.name,
        "shard_count": len(engine.memory_bank.shards),
    }


# ============================================================================
# Dev Mode Endpoints (hidden in user mode)
# ============================================================================


@router.get("/dev/parameters")
async def get_dev_parameters(
    dev_mode: Annotated[bool, Query(description="Enable dev mode access")] = False,
):
    """Get current engine parameters (dev mode only)."""
    if not dev_mode and settings.deployment_tier != DeploymentTier.DEV_ALPHA:
        raise HTTPException(status_code=403, detail="Dev mode required")

    engine = get_engine()
    params = engine.parameters

    return {
        "tau_scale_1": params.tau_scale_1,
        "tau_scale_2": params.tau_scale_2,
        "tau_scale_3": params.tau_scale_3,
        "tau_scale_4": params.tau_scale_4,
        "cleanup_k_top": params.cleanup_k_top,
        "binding_temperature": params.binding_temperature,
        "binding_strength": params.binding_strength,
        "cosine_threshold": params.cosine_threshold,
        "max_shards": params.max_shards,
    }


@router.put("/dev/parameters")
async def update_dev_parameters(
    request: DevParametersRequest,
    dev_mode: Annotated[bool, Query(description="Enable dev mode access")] = False,
):
    """Update engine parameters (dev mode only)."""
    if not dev_mode and settings.deployment_tier != DeploymentTier.DEV_ALPHA:
        raise HTTPException(status_code=403, detail="Dev mode required")

    engine = get_engine()

    # Update only provided parameters
    if request.tau_scale_1 is not None:
        engine.parameters.tau_scale_1 = request.tau_scale_1
    if request.tau_scale_2 is not None:
        engine.parameters.tau_scale_2 = request.tau_scale_2
    if request.tau_scale_3 is not None:
        engine.parameters.tau_scale_3 = request.tau_scale_3
    if request.tau_scale_4 is not None:
        engine.parameters.tau_scale_4 = request.tau_scale_4
    if request.cleanup_k_top is not None:
        engine.parameters.cleanup_k_top = request.cleanup_k_top
    if request.binding_temperature is not None:
        engine.parameters.binding_temperature = request.binding_temperature
    if request.binding_strength is not None:
        engine.parameters.binding_strength = request.binding_strength
    if request.cosine_threshold is not None:
        engine.parameters.cosine_threshold = request.cosine_threshold

    return {"status": "updated", "message": "Parameters updated successfully"}

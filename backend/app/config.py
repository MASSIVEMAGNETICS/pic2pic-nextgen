"""
Configuration settings for pic2pic-nextgen backend.
Manages deployment tiers and feature flags.
"""
from enum import Enum
from typing import Literal

from pydantic_settings import BaseSettings


class DeploymentTier(str, Enum):
    DEV_ALPHA = "dev-alpha"
    BETA_CREATOR = "beta-creator"
    PRODUCTION_V1 = "production-v1"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application metadata
    app_name: str = "pic2pic-nextgen"
    app_version: str = "2.0.0"

    # Deployment configuration
    deployment_tier: DeploymentTier = DeploymentTier.DEV_ALPHA
    debug: bool = True

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:1420", "tauri://localhost"]

    # Self-healing settings
    checkpoint_interval: int = 10  # batches
    max_memory_usage_mb: int = 4096
    cpu_temp_threshold_c: float = 85.0
    watchdog_restart_delay_s: float = 3.0
    integrity_check_interval: int = 1000  # operations
    cosine_similarity_threshold: float = 0.92

    # File storage
    upload_dir: str = "./uploads"
    checkpoint_dir: str = "./checkpoints"
    holo_presets_dir: str = "./presets"

    class Config:
        env_prefix = "PIC2PIC_"
        env_file = ".env"


settings = Settings()

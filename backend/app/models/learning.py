"""Learning system models."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    """Source of the build data."""

    AI_GENERATED = "ai_generated"
    PARSED_GW2SKILL = "parsed_gw2skill"
    COMMUNITY_SCRAPE = "community_scrape"
    USER_IMPORT = "user_import"


class QualityScore(BaseModel):
    """Quality evaluation scores."""

    synergy_score: float = Field(ge=0, le=10, description="Team synergy quality")
    role_coverage: float = Field(ge=0, le=10, description="Role distribution quality")
    boon_coverage: float = Field(ge=0, le=10, description="Boon coverage quality")
    meta_compliance: float = Field(ge=0, le=10, description="Current meta compliance")
    build_validity: float = Field(ge=0, le=10, description="Build technical validity")
    overall_score: float = Field(ge=0, le=10, description="Overall quality score")


class TrainingDatapoint(BaseModel):
    """Single training datapoint."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Build/Team data
    build_id: Optional[str] = None
    team_id: Optional[str] = None
    data: Dict = Field(default_factory=dict)  # Actual build/team data
    
    # Metadata
    game_mode: str
    profession: Optional[str] = None
    role: Optional[str] = None
    source: DataSource
    
    # Quality
    quality_scores: Optional[QualityScore] = None
    is_validated: bool = False
    validation_date: Optional[datetime] = None
    
    # Storage
    compressed_size_bytes: int = 0
    is_archived: bool = False
    archive_date: Optional[datetime] = None


class LearningStats(BaseModel):
    """Statistics for the learning system."""

    total_datapoints: int = 0
    validated_datapoints: int = 0
    archived_datapoints: int = 0
    average_quality_score: float = 0.0
    total_storage_bytes: int = 0
    
    # By source
    datapoints_by_source: Dict[str, int] = Field(default_factory=dict)
    
    # Quality distribution
    high_quality_count: int = 0  # score >= 8
    medium_quality_count: int = 0  # 5 <= score < 8
    low_quality_count: int = 0  # score < 5
    
    last_cleanup_date: Optional[datetime] = None
    last_training_date: Optional[datetime] = None


class FineTuningConfig(BaseModel):
    """Configuration for fine-tuning."""

    min_datapoints: int = Field(default=100, description="Min datapoints before training")
    min_quality_threshold: float = Field(default=7.0, description="Min quality score")
    training_interval_days: int = Field(default=7, description="Days between trainings")
    max_training_samples: int = Field(default=1000, description="Max samples per training")
    
    # Ollama fine-tuning parameters
    learning_rate: float = 0.0001
    num_epochs: int = 3
    batch_size: int = 4


class StorageConfig(BaseModel):
    """Storage management configuration."""

    max_storage_gb: float = Field(default=5.0, description="Max storage in GB")
    archive_threshold_days: int = Field(default=30, description="Days before archiving")
    delete_threshold_days: int = Field(default=90, description="Days before deletion")
    min_quality_to_keep: float = Field(default=5.0, description="Min quality to keep")
    compression_enabled: bool = True

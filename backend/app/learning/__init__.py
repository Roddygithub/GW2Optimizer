"""
Learning module for GW2Optimizer.

This module provides functionality for collecting user interaction data,
storing it locally, and preparing it for future machine learning applications.

All data collection is:
- Anonymous (no personal information)
- Local only (no external transmission)
- GDPR compliant
- Automatically purged based on configured limits

Modules:
    data: Data collection and storage
    models: ML model training and inference (future)
    utils: Utility functions for data processing
"""

from app.learning.data.collector import InteractionCollector
from app.learning.data.storage import LearningStorage

__all__ = [
    "InteractionCollector",
    "LearningStorage",
]

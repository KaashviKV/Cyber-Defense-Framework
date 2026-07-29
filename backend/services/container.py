"""
Service container for shared application dependencies.

Loads heavy objects once at startup and reuses them across requests.
"""

from typing import Optional

from backend.pipeline import CyberDefensePipeline
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class ServiceContainer:
    _pipeline: Optional[CyberDefensePipeline] = None
    _initialized: bool = False

    @classmethod
    def init(cls, eager: bool = True) -> None:
        """Initialize shared services. Called once during app startup."""
        if cls._initialized:
            return

        if eager:
            logger.info("Initializing CyberDefensePipeline singleton")
            cls._pipeline = CyberDefensePipeline()

        cls._initialized = True

    @classmethod
    def get_pipeline(cls) -> CyberDefensePipeline:
        if cls._pipeline is None:
            logger.info("Lazy-loading CyberDefensePipeline")
            cls._pipeline = CyberDefensePipeline()
            cls._initialized = True
        return cls._pipeline

    @classmethod
    def reset(cls) -> None:
        """Reset container state (primarily for tests)."""
        cls._pipeline = None
        cls._initialized = False

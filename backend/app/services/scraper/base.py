from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional


@dataclass
class ScrapedBuildData:
    """Minimal scraped build payload.

    This structure is intentionally simple so it can be reused by multiple
    scrapers (Hardstuck, Snowcrows, MetaBattle, etc.) and exposed directly
    via the API.
    """

    source_url: str
    chat_code: Optional[str]
    name: Optional[str] = None
    context: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for build scrapers."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:  # pragma: no cover - simple predicate
        """Return True if this scraper can handle the given URL."""

    @abstractmethod
    async def scrape(self, url: str) -> ScrapedBuildData:
        """Scrape a build page and return minimal build data."""
        raise NotImplementedError

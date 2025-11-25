from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, List, Optional


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
    stats_text: Optional[str] = None
    runes_text: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for build scrapers."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:  # pragma: no cover - simple predicate
        """Return True if this scraper can handle the given URL."""

    @abstractmethod
    async def scrape(self, url: str) -> ScrapedBuildData:
        """Scrape a build page and return minimal build data."""
        raise NotImplementedError

    @staticmethod
    def _search_json_recursive(data: Any, keys: List[str]) -> Optional[str]:
        if not keys:
            return None

        lowered_keys = {key.lower() for key in keys}

        def _inner(node: Any) -> Optional[str]:
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(k, str) and k.lower() in lowered_keys and isinstance(v, str):
                        return v
                    result = _inner(v)
                    if result is not None:
                        return result
            elif isinstance(node, (list, tuple)):
                for item in node:
                    result = _inner(item)
                    if result is not None:
                        return result
            return None

        return _inner(data)

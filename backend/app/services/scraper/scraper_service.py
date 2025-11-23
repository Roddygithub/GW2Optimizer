from __future__ import annotations

from typing import List

from app.core.logging import logger
from app.services.scraper.base import BaseScraper, ScrapedBuildData
from app.services.scraper.hardstuck_scraper import HardstuckScraper


class ScraperService:
    """High-level entry point for build scraping by URL.

    This service selects the appropriate scraper implementation based on the
    URL and returns a minimal, normalized payload that can be consumed by the
    API or other services.
    """

    def __init__(self, scrapers: List[BaseScraper] | None = None) -> None:
        self.scrapers: List[BaseScraper] = scrapers or [HardstuckScraper()]

    async def scrape_build(self, url: str) -> ScrapedBuildData:
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                logger.info("Using scraper", extra={"scraper": scraper.__class__.__name__, "url": url})
                return await scraper.scrape(url)

        logger.warning("No scraper available for URL", extra={"url": url})
        raise ValueError(f"No scraper available for URL: {url}")

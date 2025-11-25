from __future__ import annotations

import re
from typing import Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import logger
from app.services.scraper.base import BaseScraper, ScrapedBuildData


_CHAT_CODE_PATTERN = re.compile(r"\[&[A-Za-z0-9+/=]+\]")


class HardstuckScraper(BaseScraper):
    """Scraper for individual Hardstuck build pages.

    This scraper focuses on extracting the GW2 chat code from a build page
    and some minimal metadata (name, rough context).
    """

    def __init__(self) -> None:
        self.user_agent = settings.SCRAPER_USER_AGENT

    def can_handle(self, url: str) -> bool:
        return "hardstuck.gg" in url

    async def scrape(self, url: str) -> ScrapedBuildData:
        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        chat_code = self._extract_chat_code(soup, html)
        name = self._extract_name(soup)
        context = self._infer_context(html)
        stats_text, runes_text = self._extract_equipment_text(soup)

        if not chat_code:
            logger.warning("No chat code found on Hardstuck page", extra={"url": url})

        return ScrapedBuildData(
            source_url=url,
            chat_code=chat_code,
            name=name,
            context=context,
            stats_text=stats_text,
            runes_text=runes_text,
        )

    def _extract_chat_code(self, soup: BeautifulSoup, html: str) -> Optional[str]:
        """Try several strategies to find a GW2 build chat code on the page."""

        # 1) Look for an input element whose value looks like a chat code
        input_el = soup.find("input", attrs={"value": _CHAT_CODE_PATTERN})
        if input_el and isinstance(input_el, dict) is False:  # type: ignore[unreachable]
            # BeautifulSoup Tag behaves like a mapping but isn't a dict; we
            # only need its attributes.
            value = input_el.get("value")  # type: ignore[call-arg]
            if isinstance(value, str) and _CHAT_CODE_PATTERN.fullmatch(value):
                return value

        # 2) Fallback: search anywhere in the HTML text
        match = _CHAT_CODE_PATTERN.search(html)
        if match:
            return match.group(0)

        return None

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract build name from the main heading if possible."""

        for tag_name in ("h1", "h2"):
            title_el = soup.find(tag_name)
            if title_el:
                text = title_el.get_text(strip=True)
                if text:
                    return text
        return None

    def _infer_context(self, html: str) -> Optional[str]:
        """Very rough context heuristic based on page text."""

        lowered = html.lower()
        if "wvw" in lowered:
            return "WvW"
        if "fractals" in lowered or "fractal" in lowered:
            return "Fractals"
        if "raid" in lowered or "raids" in lowered:
            return "Raid"
        return None

    def _extract_equipment_text(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Heuristically extract equipment-related text (stats / runes).

        This is a best-effort approach: we scan common text containers and
        pick the first occurrences that mention stats/equipment or runes.
        """

        stats_text: Optional[str] = None
        runes_text: Optional[str] = None

        candidate_tags = ("p", "span", "li", "h2", "h3", "h4")
        for tag_name in candidate_tags:
            for el in soup.find_all(tag_name):
                text = el.get_text(" ", strip=True)
                if not text:
                    continue
                lowered = text.lower()

                if runes_text is None and ("rune" in lowered or "runes" in lowered):
                    runes_text = text

                if stats_text is None and (
                    "stat" in lowered
                    or "equipment" in lowered
                    or "gear" in lowered
                ):
                    stats_text = text

                if stats_text is not None and runes_text is not None:
                    break
            if stats_text is not None and runes_text is not None:
                break

        return stats_text, runes_text

from __future__ import annotations

import json
import re
from typing import Optional, Tuple
import html as html_lib

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import logger
from app.services.scraper.base import BaseScraper, ScrapedBuildData


_CHAT_CODE_PATTERN = re.compile(r"\[&[A-Za-z0-9+/=]+\]")


class SnowcrowsScraper(BaseScraper):
    """Scraper for individual Snowcrows build pages.

    Focuses on extracting the GW2 chat code plus minimal metadata.
    """

    def __init__(self) -> None:
        self.user_agent = settings.SCRAPER_USER_AGENT

    def can_handle(self, url: str) -> bool:
        return "snowcrows.com" in url

    async def scrape(self, url: str) -> ScrapedBuildData:
        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        chat_code = self._extract_chat_code(soup, html)
        name = self._extract_name(soup)
        context = self._infer_context(url, html)
        stats_text, runes_text = self._extract_equipment_text(soup)

        if not chat_code:
            logger.warning("No chat code found on Snowcrows page", extra={"url": url})

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

        # 1) Look for common attributes used by copy-to-clipboard buttons
        for tag in soup.find_all(["input", "textarea", "button", "a"]):
            for attr in ("value", "data-clipboard-text", "data-chat-code", "data-code", "data-copy-text", "onclick"):
                value = tag.get(attr)
                if isinstance(value, str):
                    decoded = html_lib.unescape(value)
                    match = _CHAT_CODE_PATTERN.search(decoded)
                    if match:
                        return match.group(0)

        # 2) Look inside script tags (e.g. Next.js __NEXT_DATA__)
        for script in soup.find_all("script"):
            if not script.string:
                continue
            text = script.string

            script_type = (script.get("type") or "").lower()
            script_id = script.get("id") or ""
            if script_type == "application/json" or script_id == "__NEXT_DATA__":
                raw = text.strip()
                if raw:
                    try:
                        data = json.loads(raw)
                    except Exception:
                        data = None
                    if data is not None:
                        value = self._search_json_recursive(
                            data,
                            ["chatCode", "chat_code", "code"],
                        )
                        if isinstance(value, str):
                            match = _CHAT_CODE_PATTERN.search(value)
                            if match:
                                return match.group(0)
                            # Some APIs store the template without the surrounding
                            # "[&" and "]". In that case, reconstruct a full
                            # chat link if the value looks like a base64 blob.
                            if re.fullmatch(r"[A-Za-z0-9+/=]{10,}", value):
                                return f"[&{value}]"

            match = _CHAT_CODE_PATTERN.search(text)
            if match:
                return match.group(0)

        # 3) Fallback: search anywhere in the raw HTML
        match = _CHAT_CODE_PATTERN.search(html)
        if match:
            return match.group(0)

        return None

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract build name from heading or title if possible."""

        for tag_name in ("h1", "h2", "title"):
            title_el = soup.find(tag_name)
            if title_el:
                text = title_el.get_text(strip=True)
                if text:
                    return text
        return None

    def _infer_context(self, url: str, html: str) -> Optional[str]:
        """Very rough context heuristic with WvW focus."""

        lowered_url = url.lower()
        if "/wvw" in lowered_url:
            return "WvW"

        lowered = html.lower()
        if "wvw" in lowered:
            return "WvW"
        if "fractals" in lowered or "fractal" in lowered:
            return "Fractals"
        if "raid" in lowered or "raids" in lowered:
            return "Raid"
        return None

    def _extract_equipment_text(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Best-effort extraction of equipment-related text (stats / runes).

        Snowcrows uses a modern UI with gear sections; here we simply scan common
        text containers and keep the first snippets mentioning stats/equipment or
        runes so they can be passed to the AI.
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

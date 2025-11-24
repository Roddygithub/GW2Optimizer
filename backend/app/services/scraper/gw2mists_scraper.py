from __future__ import annotations

import json
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import logger
from app.services.scraper.base import BaseScraper, ScrapedBuildData


_CHAT_CODE_PATTERN = re.compile(r"\[&[A-Za-z0-9+/=]{10,}\]")


class GW2MistsScraper(BaseScraper):
    """Scraper for individual GW2Mists build pages.

    GW2Mists is a modern React app; the chat code may appear in script tags
    or embedded JSON. We search broadly with a regex.
    """

    def __init__(self) -> None:
        self.user_agent = settings.SCRAPER_USER_AGENT

    def can_handle(self, url: str) -> bool:
        return "gw2mists.com" in url

    async def scrape(self, url: str) -> ScrapedBuildData:
        slug = self._extract_slug(url)

        chat_code: Optional[str] = None
        name: Optional[str] = None
        context: Optional[str] = None
        stats_text: Optional[str] = None
        runes_text: Optional[str] = None

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # 1) Try the public JSON API first if we have a slug
            if slug:
                api_url = f"https://api.gw2mists.com/v1/builds/{slug}"
                api_headers = {
                    "User-Agent": self.user_agent,
                    "Referer": url,
                    "Accept": "application/json",
                }
                try:
                    api_response = await client.get(api_url, headers=api_headers)
                    if api_response.status_code == 200:
                        text = api_response.text.strip()
                        # Some endpoints may return bare "OK" as a health-check.
                        if text and text.upper() != "OK":
                            try:
                                data = api_response.json()
                            except Exception:
                                data = None

                            if isinstance(data, (dict, list)):
                                raw_code = self._search_json_recursive(
                                    data,
                                    ["chatCode", "chat_code", "code"],
                                )
                                if isinstance(raw_code, str):
                                    match = _CHAT_CODE_PATTERN.search(raw_code)
                                    if match:
                                        chat_code = match.group(0)
                                    elif re.fullmatch(r"[A-Za-z0-9+/=]{10,}", raw_code):
                                        chat_code = f"[&{raw_code}]"

                                if not name:
                                    raw_name = self._search_json_recursive(data, ["name", "title"])
                                    if isinstance(raw_name, str) and raw_name.strip():
                                        name = raw_name.strip()

                                if stats_text is None or runes_text is None:
                                    s, r = self._extract_equipment_from_json(data)
                                    if stats_text is None and s:
                                        stats_text = s
                                    if runes_text is None and r:
                                        runes_text = r
                except Exception as exc:  # pragma: no cover - network / API issues
                    logger.warning(
                        "GW2Mists API lookup failed",
                        extra={"url": url, "slug": slug, "error": str(exc)},
                    )

            # 2) Fallback to HTML scraping if API did not yield a usable chat code
            if chat_code is None or name is None:
                headers = {"User-Agent": self.user_agent}
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                if chat_code is None:
                    chat_code = self._extract_chat_code(soup, html)
                if name is None:
                    name = self._extract_name(soup)
                context = self._infer_context(url, html)

                if stats_text is None or runes_text is None:
                    s, r = self._extract_equipment_text(soup)
                    if stats_text is None and s:
                        stats_text = s
                    if runes_text is None and r:
                        runes_text = r
            else:
                # Infer context from URL only when we didn't need HTML
                context = self._infer_context(url, "")

        if not chat_code:
            logger.warning("No chat code found on GW2Mists page", extra={"url": url})

        return ScrapedBuildData(
            source_url=url,
            chat_code=chat_code,
            name=name,
            context=context,
            stats_text=stats_text,
            runes_text=runes_text,
        )

    def _extract_chat_code(self, soup: BeautifulSoup, html: str) -> Optional[str]:
        """Find a GW2 build chat code anywhere in the page.

        For GW2Mists, the code is often surfaced in JSON data or rendered
        components, so we look inside script tags and fall back to a global
        regex on the raw HTML.
        """

        for tag in soup.find_all(["input", "textarea", "button", "a"]):
            for attr in ("value", "data-clipboard-text", "data-chat-code", "data-code", "data-copy-text"):
                value = tag.get(attr)
                if isinstance(value, str):
                    match = _CHAT_CODE_PATTERN.search(value)
                    if match:
                        return match.group(0)

        # 1) Look inside script tags
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
                            if re.fullmatch(r"[A-Za-z0-9+/=]{10,}", value):
                                return f"[&{value}]"

            match = _CHAT_CODE_PATTERN.search(text)
            if match:
                return match.group(0)

        # 2) Fallback: search anywhere in the raw HTML
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
        """Infer very rough context.

        GW2Mists is WvW-focused, so default to "WvW".
        """

        return "WvW"

    def _extract_equipment_from_json(self, data: object) -> Tuple[Optional[str], Optional[str]]:
        """Best-effort extraction of equipment-related text from the JSON API.

        We simply look for common keys that might hold stat or rune names and
        return the first string values we encounter.
        """

        stats_text: Optional[str] = None
        runes_text: Optional[str] = None

        if isinstance(data, (dict, list)):
            stats_text = self._search_json_recursive(data, ["stats", "stat", "attribute", "attributes"])
            runes_text = self._search_json_recursive(data, ["rune", "runes", "runeName", "rune_name"])

        return stats_text, runes_text

    def _extract_equipment_text(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Best-effort extraction of equipment-related text (stats / runes) from HTML."""

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

    def _extract_slug(self, url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
        except Exception:
            return None

        path = (parsed.path or "").strip("/")
        if not path:
            return None

        # Expected format: /builds/<profession>/<slug>
        if path.startswith("builds/"):
            return path[len("builds/") :]
        return path

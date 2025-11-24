from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.services.build_analysis_service import BuildAnalysisService
from app.services.gw2_chat_code import ChatCodeDecoder
from app.services.gw2_api_client import GW2APIClient
from app.services.scraper.scraper_service import ScraperService


class UrlAnalysisService:
    """High-level service: URL -> Chat Code -> Build synergy analysis.

    Pipeline:
        1. Scrape the URL to extract a GW2 build chat code.
        2. Decode the build template (profession, specs, traits, skills).
        3. Delegate synergy analysis to BuildAnalysisService.
    """

    def __init__(
        self,
        scraper_service: Optional[ScraperService] = None,
        build_analysis_service: Optional[BuildAnalysisService] = None,
        gw2_client: Optional[GW2APIClient] = None,
        decoder: Optional[ChatCodeDecoder] = None,
    ) -> None:
        self.gw2_client = gw2_client or GW2APIClient()
        self.scraper_service = scraper_service or ScraperService()
        self.build_analysis_service = build_analysis_service or BuildAnalysisService(gw2_client=self.gw2_client)
        self.decoder = decoder or ChatCodeDecoder(gw2_client=self.gw2_client)

    async def analyze_from_url(self, url: str, context: str = "WvW Zerg") -> Dict[str, Any]:
        """Scrape a build URL, decode its chat code and analyze its synergy."""

        logger.info("Analyzing build from URL", extra={"url": url, "context": context})

        scraped = await self.scraper_service.scrape_build(url)
        if not scraped.chat_code:
            # Message clair consommé par l'endpoint /ai/analyze/url (400 Bad Request)
            raise ValueError(
                "URL non supportée ou aucun code de build (chat code) détecté sur la page fournie."
            )

        decoded = await self.decoder.decode_build(scraped.chat_code)

        specialization_id = decoded.get("specialization_id")
        trait_ids: List[int] = decoded.get("trait_ids") or []
        skill_ids: List[int] = decoded.get("skill_ids") or []

        equipment_summary: Optional[Dict[str, Any]] = None
        if getattr(scraped, "stats_text", None) or getattr(scraped, "runes_text", None):
            summary: Dict[str, Any] = {}
            if scraped.stats_text:
                summary["stats_text"] = scraped.stats_text
            if scraped.runes_text:
                summary["runes_text"] = scraped.runes_text
            if summary:
                equipment_summary = summary

        try:
            analysis = await self.build_analysis_service.analyze_build_synergy(
                specialization_id=specialization_id,
                trait_ids=trait_ids,
                skill_ids=skill_ids,
                context=context,
                equipment_summary=equipment_summary,
            )
        except RuntimeError as e:
            error_message = str(e) or "AI build analysis failed"
            logger.error(
                "AI build analysis failed for URL",
                extra={"url": url, "context": context, "error": error_message},
            )

            lowered = error_message.lower()
            is_timeout = "timeout" in lowered
            synergy_score = "N/A (Timeout)" if is_timeout else "N/A"
            user_error = (
                "IA trop lente, réessayez plus tard"
                if is_timeout
                else "IA indisponible ou en erreur, réessayez plus tard"
            )

            analysis = {
                "context": context,
                "synergy_score": synergy_score,
                "strengths": None,
                "weaknesses": None,
                "summary": None,
                "error": user_error,
                "error_detail": error_message,
            }

        return {
            "source": {
                "url": scraped.source_url,
                "name": scraped.name,
                "context": scraped.context or context,
                "chat_code": scraped.chat_code,
                "stats_text": getattr(scraped, "stats_text", None),
                "runes_text": getattr(scraped, "runes_text", None),
            },
            "decoded": decoded,
            "analysis": analysis,
        }

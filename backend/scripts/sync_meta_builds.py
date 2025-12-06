import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.core.config import settings
from app.core.logging import logger
from app.services.scraper.scraper_service import ScraperService
from app.services.gw2_chat_code import ChatCodeDecoder


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "learning" / "external" / "meta_build_sources_wvw.json"
OUTPUT_PATH = BASE_DIR / "data" / "learning" / "external" / "meta_builds_wvw.json"


async def _fetch_html(url: str) -> str:
    headers = {"User-Agent": settings.SCRAPER_USER_AGENT}
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


async def _discover_build_urls_from_index(url: str) -> List[str]:
    html = await _fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    urls: Set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not isinstance(href, str):
            continue
        full = urljoin(url, href)
        if "hardstuck.gg" in full and "/gw2/builds/" in full:
            urls.add(full.split("#")[0])
        elif "snowcrows.com" in full and "/builds/wvw/" in full:
            urls.add(full.split("#")[0])
        elif "guildjen.com" in full and ("wvw-" in full or "wvw-build" in full):
            urls.add(full.split("#")[0])

    return sorted(urls)


async def _process_single_build(
    scraper: ScraperService,
    decoder: ChatCodeDecoder,
    gw2_client: Any,
    raw: Dict[str, Any],
    meta_id: str,
    url: str,
) -> Optional[Dict[str, Any]]:
    try:
        scraped = await scraper.scrape_build(url)
    except Exception as e:
        logger.error("Failed to scrape meta build", extra={"url": url, "error": str(e)})
        return None

    chat_code = scraped.chat_code
    if not isinstance(chat_code, str) or not chat_code:
        logger.error("No chat code found for meta build", extra={"url": url})
        return None

    try:
        decoded = await decoder.decode_build(chat_code)
    except Exception as e:
        logger.error("Failed to decode chat code for meta build", extra={"url": url, "error": str(e)})
        return None

    spec_id = decoded.get("specialization_id")
    profession = None
    specialization = None
    if isinstance(spec_id, int) and spec_id:
        try:
            spec_data = await gw2_client.get_specialization_details(spec_id)
        except Exception as e:
            logger.error("Failed to load specialization for meta build", extra={"spec_id": spec_id, "error": str(e)})
            spec_data = None
        if isinstance(spec_data, dict):
            specialization = spec_data.get("name")
            profession = spec_data.get("profession")

    name = raw.get("name") or scraped.name or specialization or meta_id
    game_mode = raw.get("game_mode") or scraped.context or "Unknown"
    role = raw.get("role") or "unknown"
    source = raw.get("source") or "external"
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []

    return {
        "id": meta_id,
        "name": name,
        "profession": profession or "Unknown",
        "specialization": specialization or "Unknown",
        "role": str(role),
        "game_mode": str(game_mode),
        "source": source,
        "tags": tags,
        "notes": raw.get("notes"),
        "chat_code": chat_code,
        "stats_text": scraped.stats_text,
        "runes_text": scraped.runes_text,
    }


async def sync_from_config() -> None:
    if not CONFIG_PATH.is_file():
        logger.error("Meta build sources config not found", extra={"path": str(CONFIG_PATH)})
        return

    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to read meta build sources config", extra={"error": str(e)})
        return

    items = config.get("builds") if isinstance(config, dict) else None
    if not isinstance(items, list):
        logger.error("Meta build sources config has no 'builds' list")
        return

    scraper = ScraperService()
    decoder = ChatCodeDecoder()
    gw2_client = decoder.gw2_client

    out_builds: List[Dict[str, Any]] = []
    processed_urls: Set[str] = set()
    counter = 0

    for raw in items:
        if not isinstance(raw, dict):
            continue
        url = raw.get("url")
        if not isinstance(url, str) or not url:
            continue
        kind = raw.get("kind") or "build"
        base_id = raw.get("id") or f"meta-{counter + 1}"

        if kind == "index":
            try:
                discovered = await _discover_build_urls_from_index(url)
            except Exception as e:
                logger.error("Failed to crawl index for meta builds", extra={"url": url, "error": str(e)})
                continue
            for build_url in discovered:
                if build_url in processed_urls:
                    continue
                processed_urls.add(build_url)
                meta_id = build_url
                counter += 1
                entry = await _process_single_build(scraper, decoder, gw2_client, raw, meta_id, build_url)
                if entry is not None:
                    out_builds.append(entry)
        else:
            if url in processed_urls:
                continue
            processed_urls.add(url)
            meta_id = base_id
            counter += 1
            entry = await _process_single_build(scraper, decoder, gw2_client, raw, meta_id, url)
            if entry is not None:
                out_builds.append(entry)

    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "builds": out_builds,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Meta builds synced", extra={"count": len(out_builds), "output": str(OUTPUT_PATH)})


def main() -> None:
    asyncio.run(sync_from_config())


if __name__ == "__main__":
    main()

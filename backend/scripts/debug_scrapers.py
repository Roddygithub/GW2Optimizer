from __future__ import annotations

import asyncio

from app.services.scraper.scraper_service import ScraperService
from app.services.gw2_chat_code import ChatCodeDecoder


URLS = [
    ("Hardstuck", "https://hardstuck.gg/gw2/builds/guardian/heal-firebrand/"),
    ("Snowcrows", "https://snowcrows.com/builds/wvw/elementalist/power-tempest"),
    ("GW2Mists", "https://gw2mists.com/builds/guardian/support-firebrand"),
    ("GuildJen", "https://guildjen.com/s-d-daredevil-roaming-build/"),
]


async def main() -> None:
    scraper = ScraperService()
    decoder = ChatCodeDecoder()

    for label, url in URLS:
        print("====", label, "====")
        try:
            scraped = await scraper.scrape_build(url)
        except Exception as e:  # pragma: no cover - manual debug script
            print("ERROR_SCRAPE:", type(e).__name__, str(e))
            continue

        print("URL:", url)
        print("NAME:", scraped.name)
        print("CHAT_CODE:", scraped.chat_code)
        print("STATS_TEXT:", getattr(scraped, "stats_text", None))
        print("RUNES_TEXT:", getattr(scraped, "runes_text", None))

        if not scraped.chat_code:
            print("DECODE_SKIPPED: no chat code found")
            continue

        try:
            decoded = await decoder.decode_build(scraped.chat_code)
        except Exception as e:  # pragma: no cover - manual debug script
            print("ERROR_DECODE:", type(e).__name__, str(e))
            continue

        print("SPECIALIZATION_ID:", decoded.get("specialization_id"))
        print("TRAIT_IDS_LEN:", len(decoded.get("trait_ids") or []))
        print("SKILL_IDS_LEN:", len(decoded.get("skill_ids") or []))


if __name__ == "__main__":
    asyncio.run(main())

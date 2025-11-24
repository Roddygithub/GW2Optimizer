from __future__ import annotations

import asyncio

from app.services.scraper.hardstuck_scraper import HardstuckScraper


URL = "https://hardstuck.gg/gw2/builds/guardian/heal-firebrand/"


async def main() -> None:
  scraper = HardstuckScraper()

  print("=== Hardstuck stats verification ===")
  print("URL:", URL)

  try:
    scraped = await scraper.scrape(URL)
  except Exception as e:  # pragma: no cover - manual debug script
    print("ERROR_SCRAPE:", type(e).__name__, str(e))
    return

  print("NAME:", scraped.name)
  print("CHAT_CODE:", scraped.chat_code)
  print("STATS_TEXT:", getattr(scraped, "stats_text", None))
  print("RUNES_TEXT:", getattr(scraped, "runes_text", None))


if __name__ == "__main__":
  asyncio.run(main())

"""Scraper API endpoints."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.logging import logger
from app.models.learning import DataSource
from app.services.learning.data_collector import DataCollector
from app.services.scraper.community_scraper import CommunityScraper

router = APIRouter()


@router.post("/scraper/run")
async def run_scraper(background_tasks: BackgroundTasks) -> dict:
    """
    Trigger community scraping manually.
    
    Scrapes:
    - Snowcrows (raid builds)
    - MetaBattle (WvW builds)
    - Hardstuck (WvW builds)
    
    All scraped builds are automatically collected for learning.
    """
    try:
        async def scrape_task() -> None:
            scraper = CommunityScraper()
            collector = DataCollector()
            
            logger.info("🚀 Starting community scraping...")
            builds = await scraper.scrape_all_sources()
            
            # Collect all scraped builds for learning
            collected = 0
            for build in builds:
                try:
                    await collector.collect_build(build, DataSource.COMMUNITY_SCRAPE)
                    collected += 1
                except Exception as e:
                    logger.error(f"Failed to collect scraped build: {e}")
            
            logger.info(f"✅ Scraping completed: {len(builds)} builds found, {collected} collected")
        
        background_tasks.add_task(scrape_task)
        
        return {
            "status": "started",
            "message": "Community scraping triggered in background",
        }
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/scraper/sources")
async def get_sources() -> dict:
    """Get list of scraping sources."""
    scraper = CommunityScraper()
    return {
        "sources": list(scraper.sources.keys()),
        "urls": scraper.sources,
    }

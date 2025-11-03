"""Community websites scraper for builds."""

import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import logger
from app.models.build import Build, GameMode, Profession, Role


class CommunityScraper:
    """Scraper for community build websites."""

    def __init__(self) -> None:
        """Initialize community scraper."""
        self.sources = {
            "snowcrows": "https://snowcrows.com/builds",
            "metabattle": "https://metabattle.com/wiki/WvW",
            "hardstuck": "https://hardstuck.gg/gw2/builds/",
            "guildjen": "https://guildjen.com/builds/",
        }
        self.user_agent = settings.SCRAPER_USER_AGENT
        self.profession_map = {
            "guardian": Profession.GUARDIAN,
            "revenant": Profession.REVENANT,
            "warrior": Profession.WARRIOR,
            "engineer": Profession.ENGINEER,
            "ranger": Profession.RANGER,
            "thief": Profession.THIEF,
            "elementalist": Profession.ELEMENTALIST,
            "mesmer": Profession.MESMER,
            "necromancer": Profession.NECROMANCER,
        }

    async def scrape_all_sources(self) -> List[Build]:
        """
        Scrape all community sources for builds.

        Returns:
            List of scraped builds
        """
        all_builds = []

        # Scrape each source with specific scraper
        scrapers = [
            ("Snowcrows", self.scrape_snowcrows),
            ("MetaBattle", self.scrape_metabattle),
            ("Hardstuck", self.scrape_hardstuck),
        ]

        for source_name, scraper_func in scrapers:
            try:
                builds = await scraper_func()
                all_builds.extend(builds)
                logger.info(f"✅ Scraped {len(builds)} builds from {source_name}")
            except Exception as e:
                logger.error(f"❌ Error scraping {source_name}: {e}")

        # Remove duplicates based on name and profession
        unique_builds = self._remove_duplicates(all_builds)
        logger.info(f"📊 Total unique builds: {len(unique_builds)} from {len(all_builds)} scraped")

        return unique_builds

    async def _scrape_source(self, url: str) -> List[Build]:
        """
        Scrape a specific source.

        Args:
            url: Source URL

        Returns:
            List of builds from this source
        """
        # TODO: Implement specific scrapers for each source
        # This is a placeholder implementation
        logger.info(f"Scraping {url}...")

        try:
            headers = {"User-Agent": self.user_agent}
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                # Placeholder: Each source needs custom parsing logic
                # based on their HTML structure

                return []

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

    async def scrape_snowcrows(self) -> List[Build]:
        """Scrape Snowcrows for raid builds."""
        builds = []

        try:
            url = self.sources["snowcrows"]
            headers = {"User-Agent": self.user_agent}

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Snowcrows structure: look for build cards/links
                build_links = soup.find_all("a", href=re.compile(r"/builds?/"))

                for link in build_links[:20]:  # Limit to 20 builds
                    try:
                        build_url = link.get("href", "")
                        if not build_url.startswith("http"):
                            build_url = f"https://snowcrows.com{build_url}"

                        # Extract build name and profession from link text or URL
                        build_name = link.get_text(strip=True)
                        profession = self._extract_profession_from_text(build_name)

                        if profession and build_name:
                            build = Build(
                                name=f"{build_name} (Snowcrows)",
                                profession=profession,
                                game_mode=GameMode.RAID_GUILD,  # Snowcrows = raids
                                role=self._guess_role_from_name(build_name),
                                source_url=build_url,
                                source_type="snowcrows",
                                description=f"Raid build from Snowcrows - {build_name}",
                            )
                            builds.append(build)

                    except Exception as e:
                        logger.debug(f"Error parsing Snowcrows build: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping Snowcrows: {e}")

        return builds

    async def scrape_metabattle(self) -> List[Build]:
        """Scrape MetaBattle for WvW builds."""
        builds = []

        try:
            url = self.sources["metabattle"]
            headers = {"User-Agent": self.user_agent}

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # MetaBattle structure: look for build entries
                build_entries = soup.find_all(["div", "article"], class_=re.compile(r"build|entry"))

                for entry in build_entries[:20]:  # Limit to 20
                    try:
                        # Find build link
                        link = entry.find("a", href=True)
                        if not link:
                            continue

                        build_url = link["href"]
                        if not build_url.startswith("http"):
                            build_url = f"https://metabattle.com{build_url}"

                        build_name = link.get_text(strip=True)
                        profession = self._extract_profession_from_text(build_name)

                        if profession and build_name:
                            # MetaBattle has various game modes
                            game_mode = GameMode.ZERG  # Default WvW
                            if "roam" in build_name.lower():
                                game_mode = GameMode.ROAMING

                            build = Build(
                                name=f"{build_name} (MetaBattle)",
                                profession=profession,
                                game_mode=game_mode,
                                role=self._guess_role_from_name(build_name),
                                source_url=build_url,
                                source_type="metabattle",
                                description=f"WvW build from MetaBattle - {build_name}",
                            )
                            builds.append(build)

                    except Exception as e:
                        logger.debug(f"Error parsing MetaBattle build: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping MetaBattle: {e}")

        return builds

    async def scrape_hardstuck(self) -> List[Build]:
        """Scrape Hardstuck for WvW builds."""
        builds = []

        try:
            url = self.sources["hardstuck"]
            headers = {"User-Agent": self.user_agent}

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Hardstuck structure: look for build cards
                build_cards = soup.find_all(["div", "article"], class_=re.compile(r"build|card"))

                for card in build_cards[:20]:  # Limit to 20
                    try:
                        link = card.find("a", href=True)
                        if not link:
                            continue

                        build_url = link["href"]
                        if not build_url.startswith("http"):
                            build_url = f"https://hardstuck.gg{build_url}"

                        build_name = link.get_text(strip=True)
                        profession = self._extract_profession_from_text(build_name)

                        if profession and build_name:
                            build = Build(
                                name=f"{build_name} (Hardstuck)",
                                profession=profession,
                                game_mode=GameMode.ZERG,  # Hardstuck focuses on WvW
                                role=self._guess_role_from_name(build_name),
                                source_url=build_url,
                                source_type="hardstuck",
                                description=f"WvW build from Hardstuck - {build_name}",
                            )
                            builds.append(build)

                    except Exception as e:
                        logger.debug(f"Error parsing Hardstuck build: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping Hardstuck: {e}")

        return builds

    def _extract_profession_from_text(self, text: str) -> Optional[Profession]:
        """Extract profession from text."""
        text_lower = text.lower()

        for prof_name, prof_enum in self.profession_map.items():
            if prof_name in text_lower:
                return prof_enum

        return None

    def _guess_role_from_name(self, name: str) -> Role:
        """Guess role from build name."""
        name_lower = name.lower()

        # Role keywords
        if any(word in name_lower for word in ["heal", "support", "cleric", "minstrel"]):
            return Role.SUPPORT
        elif any(word in name_lower for word in ["tank", "frontline", "melee"]):
            return Role.TANK
        elif any(word in name_lower for word in ["dps", "damage", "power", "condi"]):
            return Role.DPS
        elif any(word in name_lower for word in ["boon", "quickness", "alacrity"]):
            return Role.BOONSHARE
        else:
            return Role.DPS  # Default

    def _remove_duplicates(self, builds: List[Build]) -> List[Build]:
        """Remove duplicate builds based on name and profession."""
        seen = set()
        unique_builds = []

        for build in builds:
            # Normalize profession which may already be a string depending on model config
            profession_value = getattr(build.profession, "value", build.profession)

            # Create unique key
            key = (build.name.lower(), str(profession_value).lower())

            if key not in seen:
                seen.add(key)
                unique_builds.append(build)

        return unique_builds

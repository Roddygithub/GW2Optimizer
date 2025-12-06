"""GW2Skill URL parser - Complete implementation."""

import re
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.logging import logger
from app.models.build import Build, GameMode, Profession, Role, TraitLine, Skill, Equipment
from app.services.parser.gw2_data import STAT_COMBOS, EQUIPMENT_SLOTS
from app.services.ai.ollama_service import OllamaService


class GW2SkillParser:
    """Parser for GW2Skill build URLs."""

    def __init__(self, ai_service: Optional[OllamaService] = None) -> None:
        # Ollama service is only used for AI-based fallback when the profession
        # cannot be inferred from the URL. Existing behavior (HTML parsing for
        # traits/skills/gear) remains unchanged.
        self._ollama = ai_service or OllamaService()

    # Profession name mappings
    PROFESSION_MAP = {
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

    # URL format patterns
    URL_PATTERNS = [
        r"gw2skills\.net/editor/",
        r"en\.gw2skills\.net/editor/",
        r"fr\.gw2skills\.net/editor/",
        r"de\.gw2skills\.net/editor/",
    ]

    async def parse_url(self, url: str) -> Optional[Build]:
        """
        Parse a GW2Skill URL and extract build information.

        Args:
            url: GW2Skill URL

        Returns:
            Build object or None if parsing fails
        """
        try:
            # Normalize URL
            url = self._normalize_url(url)
            logger.info(f"Parsing GW2Skill URL: {url}")

            # Parse URL components (parse_qs result not used in current implementation)
            parsed = urlparse(url)
            _ = parse_qs(parsed.query)  # Result not used, but parsing for future use

            # Extract profession from URL path if possible
            profession = self._extract_profession(url)

            # Try to fetch and parse the page (traits/skills/gear from HTML)
            build_data = await self._fetch_build_page(url)

            # If profession could not be inferred from the URL (typical for
            # compressed GW2Skills URLs like ?PWwAk...), try an AI-based
            # fallback by reading the page like a human.
            if not profession:
                logger.info("GW2SkillParser: falling back to AI-based profession inference from page HTML")
                profession = await self._infer_profession_from_page(url)
                if not profession:
                    logger.error("Could not determine profession from GW2Skills page (URL + AI fallback failed)")
                    return await self._plan_b_from_page(url)

            # Create a fully valid Build object.
            # Note: id/user_id/created_at/updated_at are not present in the
            # GW2Skills data, so we generate reasonable defaults here. These
            # builds are not persisted to the main DB; they are used for
            # in-memory analysis and optional learning traces.
            now = datetime.utcnow()
            build = Build(
                id=str(uuid4()),
                user_id="gw2skill-import",
                created_at=now,
                updated_at=now,
                name=build_data.get("name", f"{profession.value} Build"),
                profession=profession,
                specialization=None,
                game_mode=GameMode.ZERG,  # Default, can be analyzed later
                role=Role.DPS,  # Default, can be analyzed later
                description=build_data.get("description"),
                playstyle=None,
                source_url=url,
                source_type="gw2skill",
                effectiveness=None,
                difficulty=None,
                is_public=False,
                trait_lines=build_data.get("trait_lines", []),
                skills=build_data.get("skills", []),
                equipment=build_data.get("equipment", []),
                synergies=[],
                counters=[],
            )

            logger.info(f"Successfully parsed build: {build.name}")
            return build

        except Exception as e:
            logger.error(f"Error parsing GW2Skill URL: {e}")
            return await self._plan_b_from_page(url)

    def _normalize_url(self, url: str) -> str:
        """Normalize GW2Skill URL to standard format."""
        # Ensure https
        if not url.startswith("http"):
            url = "https://" + url

        # Normalize domain variations
        url = url.replace("en.gw2skills.net", "gw2skills.net")
        url = url.replace("fr.gw2skills.net", "gw2skills.net")
        url = url.replace("de.gw2skills.net", "gw2skills.net")
        url = url.replace("www.gw2skills.net", "gw2skills.net")
        url = url.replace("http://", "https://")

        return url

    def _extract_profession(self, url: str) -> Optional[Profession]:
        """Extract profession from URL."""
        url_lower = url.lower()

        for prof_name, prof_enum in self.PROFESSION_MAP.items():
            if prof_name in url_lower:
                return prof_enum

        return None

    async def _infer_profession_from_page(self, url: str) -> Optional[Profession]:
        """Infer profession from GW2Skills page HTML using AI as a fallback.

        This is used when the URL does not contain the profession name (new
        compressed formats). It fetches the page, extracts readable text and
        asks the local Ollama model to pick the most likely GW2 profession.
        """

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text(separator="\n")
        except Exception as e:  # pragma: no cover - réseau non testé en CI
            logger.error(f"GW2SkillParser: failed to fetch page for AI profession inference: {e}")
            return None

        # Tronquer le texte pour éviter un prompt inutilement énorme et
        # garder l'inférence de profession raisonnablement rapide.
        # 2000 caractères suffisent largement pour que le modèle voie les
        # éléments clés de la page (titres, labels, textes autour du build).
        snippet = page_text[:2000]

        system_prompt = (
            "Tu es un expert Guild Wars 2. On te donne le TEXTE BRUT d'une page "
            "GW2Skills Build Editor (sans structure HTML). Ta tâche est de "
            "déterminer la PROFESSION principale du build parmi la liste "
            "suivante: Guardian, Revenant, Warrior, Engineer, Ranger, Thief, "
            "Elementalist, Mesmer, Necromancer.\n\n"
            "Réponds UNIQUEMENT en JSON strictement valide, sans texte autour, "
            "au format: {\"profession\": \"Guardian\"}."
        )

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "profession": {
                    "type": "string",
                    "enum": [
                        "Guardian",
                        "Revenant",
                        "Warrior",
                        "Engineer",
                        "Ranger",
                        "Thief",
                        "Elementalist",
                        "Mesmer",
                        "Necromancer",
                    ],
                }
            },
            "required": ["profession"],
            "additionalProperties": False,
        }

        try:
            ai_result = await self._ollama.generate_structured(
                prompt=snippet,
                system_prompt=system_prompt,
                schema=schema,
                max_tokens=128,
            )
        except Exception as e:  # pragma: no cover - dépendant d'Ollama
            logger.error(f"GW2SkillParser: AI profession inference failed: {e}")
            return None

        if not isinstance(ai_result, dict):
            logger.warning("GW2SkillParser: AI result for profession inference is not a dict")
            return None

        prof_str = ai_result.get("profession")
        if not isinstance(prof_str, str):
            logger.warning("GW2SkillParser: AI result missing 'profession' field")
            return None

        raw_key = prof_str.strip().lower()
        synonyms = {
            "gardien": "guardian",
            "guerrier": "warrior",
            "rôdeur": "ranger",
            "rodeur": "ranger",
            "nécromant": "necromancer",
            "necromant": "necromancer",
            "voleur": "thief",
            "ingénieur": "engineer",
            "ingenieur": "engineer",
            "envoûteur": "mesmer",
            "envouteur": "mesmer",
            "revenant": "revenant",
            "élémentaliste": "elementalist",
            "elementaliste": "elementalist",
        }
        key = synonyms.get(raw_key, raw_key)
        profession = self.PROFESSION_MAP.get(key)
        if not profession:
            logger.warning("GW2SkillParser: AI returned unknown profession '%s'", prof_str)
            return None

        return profession

    async def _plan_b_from_page(self, url: str) -> Optional[Build]:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text(separator="\n")
        except Exception as e:
            logger.error("GW2SkillParser: Plan B failed to fetch page", extra={"error": str(e)})
            return None

        snippet = page_text[:3000]

        system_prompt = (
            "Tu es un expert Guild Wars 2 WvW. On te donne le TEXTE BRUT d'une page "
            "GW2Skills Build Editor. Tu dois deviner le profil global du build "
            "(profession, spécialisation, rôle principal, mode de jeu) et produire "
            "un résumé court.\n\n"
            "Réponds UNIQUEMENT en JSON strictement valide, sans texte autour."
        )

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "profession": {
                    "type": "string",
                    "enum": [
                        "Guardian",
                        "Revenant",
                        "Warrior",
                        "Engineer",
                        "Ranger",
                        "Thief",
                        "Elementalist",
                        "Mesmer",
                        "Necromancer",
                    ],
                },
                "specialization": {"type": "string"},
                "role": {"type": "string"},
                "game_mode": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["profession"],
            "additionalProperties": True,
        }

        try:
            ai_result = await self._ollama.generate_structured(
                prompt=snippet,
                system_prompt=system_prompt,
                schema=schema,
                max_tokens=512,
            )
        except Exception as e:
            logger.error("GW2SkillParser: Plan B AI failed", extra={"error": str(e)})
            return None

        if not isinstance(ai_result, dict):
            return None

        prof_str = ai_result.get("profession")
        if not isinstance(prof_str, str):
            return None

        raw_key = prof_str.strip().lower()
        synonyms = {
            "gardien": "guardian",
            "guerrier": "warrior",
            "rôdeur": "ranger",
            "rodeur": "ranger",
            "nécromant": "necromancer",
            "necromant": "necromancer",
            "voleur": "thief",
            "ingénieur": "engineer",
            "ingenieur": "engineer",
            "envoûteur": "mesmer",
            "envouteur": "mesmer",
            "revenant": "revenant",
            "élémentaliste": "elementalist",
            "elementaliste": "elementalist",
        }
        key = synonyms.get(raw_key, raw_key)
        profession = self.PROFESSION_MAP.get(key)
        if not profession:
            return None

        role_enum = Role.DPS
        role_str = ai_result.get("role")
        if isinstance(role_str, str):
            r = role_str.strip().lower()
            if "heal" in r:
                role_enum = Role.HEALER
            elif "support" in r:
                role_enum = Role.SUPPORT
            elif "boon" in r:
                role_enum = Role.BOONSHARE
            elif "util" in r:
                role_enum = Role.UTILITY
            elif "dps" in r or "damage" in r:
                role_enum = Role.DPS

        game_mode_enum = GameMode.ZERG
        gm_str = ai_result.get("game_mode")
        if isinstance(gm_str, str):
            g = gm_str.strip().lower()
            if "roam" in g or "small" in g:
                game_mode_enum = GameMode.ROAMING
            elif "raid" in g or "gvg" in g:
                game_mode_enum = GameMode.RAID_GUILD
            elif "zerg" in g or "blob" in g:
                game_mode_enum = GameMode.ZERG

        name = ai_result.get("name")
        if not isinstance(name, str) or not name.strip():
            name = "Imported Build (Plan B)"

        description = ai_result.get("description")
        if not isinstance(description, str):
            description = None

        now = datetime.utcnow()

        trait_lines: List[TraitLine] = []
        for i in range(3):
            trait_lines.append(TraitLine(id=i, name=f"Trait Line {i + 1}", traits=[]))

        skills: List[Skill] = []
        skill_slots = ["Heal", "Utility1", "Utility2", "Utility3", "Elite"]
        for slot in skill_slots:
            skills.append(Skill(slot=slot, id=0, name=f"{slot} Skill"))

        equipment: List[Equipment] = []
        for slot in EQUIPMENT_SLOTS[:6]:
            equipment.append(Equipment(slot=slot, id=0, name=f"{slot}", stats="Berserker", rune_or_sigil=None))

        build = Build(
            id=str(uuid4()),
            user_id="gw2skill-planb",
            created_at=now,
            updated_at=now,
            name=name,
            profession=profession,
            specialization=ai_result.get("specialization"),
            game_mode=game_mode_enum,
            role=role_enum,
            description=description,
            playstyle=None,
            source_url=url,
            source_type="gw2skill-planb",
            effectiveness=None,
            difficulty=None,
            is_public=False,
            trait_lines=trait_lines,
            skills=skills,
            equipment=equipment,
            synergies=[],
            counters=[],
        )

        return build

    async def _fetch_build_page(self, url: str) -> dict:
        """
        Fetch and parse GW2Skill build page.

        Args:
            url: GW2Skill URL

        Returns:
            Dictionary with build data
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Extract build name
                name = self._extract_build_name(soup)

                # Parse URL parameters for build code
                parsed_url = urlparse(url)
                params = parse_qs(parsed_url.query)

                # Extract trait lines from URL or page
                trait_lines = self._parse_trait_lines(soup, params)

                # Extract skills
                skills = self._parse_skills(soup, params)

                # Extract equipment
                equipment = self._parse_equipment(soup, params)

                return {
                    "name": name,
                    "trait_lines": trait_lines,
                    "skills": skills,
                    "equipment": equipment,
                    "description": f"Imported from GW2Skill - {len(trait_lines)} trait lines, {len(skills)} skills",
                }

        except Exception as e:
            logger.error(f"Error fetching build page: {e}")
            return {
                "name": "Imported Build",
                "trait_lines": [],
                "skills": [],
                "equipment": [],
            }

    def _extract_build_name(self, soup: BeautifulSoup) -> str:
        """Extract build name from page."""
        # Try title tag
        title_elem = soup.find("title")
        if title_elem:
            title = title_elem.text.strip()
            # Clean up title
            title = title.replace("GW2Skills.net", "").strip()
            title = title.replace("- Guild Wars 2", "").strip()
            if title and title != "-":
                return title

        # Try meta tags
        meta_title = soup.find("meta", {"property": "og:title"})
        if meta_title and meta_title.get("content"):
            return meta_title["content"].strip()

        return "Imported Build"

    def _parse_trait_lines(self, soup: BeautifulSoup, params: Dict) -> List[TraitLine]:
        """Parse trait lines from page or URL parameters."""
        trait_lines = []

        try:
            # Look for trait line data in page scripts or data attributes
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "trait" in script.string.lower():
                    # Try to extract trait data from JavaScript
                    trait_data = self._extract_trait_data_from_script(script.string)
                    if trait_data:
                        trait_lines.extend(trait_data)

            # If no traits found, create placeholder structure
            if not trait_lines:
                logger.warning("No trait lines found in page, creating placeholders")
                for i in range(3):
                    trait_lines.append(TraitLine(id=i, name=f"Trait Line {i + 1}", traits=[]))

        except Exception as e:
            logger.error(f"Error parsing trait lines: {e}")

        return trait_lines

    def _extract_trait_data_from_script(self, script_content: str) -> List[TraitLine]:
        """Extract trait data from JavaScript content."""
        trait_lines = []

        # Look for trait patterns in script
        # GW2Skills typically stores build data in JavaScript variables
        trait_pattern = r"trait[s]?\s*[=:]\s*\[([^\]]+)\]"
        matches = re.findall(trait_pattern, script_content, re.IGNORECASE)

        for match in matches:
            # Parse trait IDs
            trait_ids = re.findall(r"\d+", match)
            if trait_ids:
                trait_lines.append(
                    TraitLine(
                        id=len(trait_lines),
                        name=f"Trait Line {len(trait_lines) + 1}",
                        traits=[int(tid) for tid in trait_ids[:3]],  # Max 3 traits per line
                    )
                )

        return trait_lines

    def _parse_skills(self, soup: BeautifulSoup, params: Dict) -> List[Skill]:
        """Parse skills from page or URL parameters."""
        skills = []

        try:
            # Look for skill data in scripts
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "skill" in script.string.lower():
                    skill_data = self._extract_skill_data_from_script(script.string)
                    if skill_data:
                        skills.extend(skill_data)

            # Standard skill slots
            skill_slots = ["Heal", "Utility1", "Utility2", "Utility3", "Elite"]

            # If no skills found, create placeholders
            if not skills:
                for slot in skill_slots:
                    skills.append(Skill(slot=slot, id=0, name=f"{slot} Skill"))

        except Exception as e:
            logger.error(f"Error parsing skills: {e}")

        return skills

    def _extract_skill_data_from_script(self, script_content: str) -> List[Skill]:
        """Extract skill data from JavaScript content."""
        skills = []
        skill_slots = ["Heal", "Utility1", "Utility2", "Utility3", "Elite"]

        # Look for skill IDs in script
        skill_pattern = r"skill[s]?\s*[=:]\s*\[([^\]]+)\]"
        matches = re.findall(skill_pattern, script_content, re.IGNORECASE)

        for match in matches:
            skill_ids = re.findall(r"\d+", match)
            for idx, skill_id in enumerate(skill_ids[:5]):
                skills.append(
                    Skill(
                        slot=skill_slots[idx] if idx < len(skill_slots) else f"Skill {idx + 1}",
                        id=int(skill_id),
                        name=f"Skill {skill_id}",
                    )
                )

        return skills

    def _parse_equipment(self, soup: BeautifulSoup, params: Dict) -> List[Equipment]:
        """Parse equipment from page or URL parameters."""
        equipment = []

        try:
            # Look for equipment data
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and ("equipment" in script.string.lower() or "gear" in script.string.lower()):
                    equip_data = self._extract_equipment_data_from_script(script.string)
                    if equip_data:
                        equipment.extend(equip_data)

            # If no equipment found, create basic structure
            if not equipment:
                for slot in EQUIPMENT_SLOTS[:6]:  # Armor slots
                    equipment.append(Equipment(slot=slot, id=0, name=f"{slot}", stats="Berserker", rune_or_sigil=None))

        except Exception as e:
            logger.error(f"Error parsing equipment: {e}")

        return equipment

    def _extract_equipment_data_from_script(self, script_content: str) -> List[Equipment]:
        """Extract equipment data from JavaScript content."""
        equipment = []

        # Look for stat combinations
        for stat_name in STAT_COMBOS.keys():
            if stat_name.lower() in script_content.lower():
                # Found a stat combo, create equipment with it
                for slot in EQUIPMENT_SLOTS[:6]:
                    equipment.append(Equipment(slot=slot, id=0, name=f"{slot}", stats=stat_name, rune_or_sigil=None))
                break

        return equipment

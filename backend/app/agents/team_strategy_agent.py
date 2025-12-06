"""
TeamStrategyAgent - LLM-based strategist for team compositions.

This agent is responsible for deciding the high-level composition
(classes, specializations, roles, and optional weapon preferences)
from a natural language user request, leveraging MetaRAGService
for meta-based context and Ollama/Mistral for reasoning.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from app.core.logging import logger
from app.models.team_strategy import TeamStrategyPlan, TeamStrategyRequest
from app.services.ai.ollama_service import OllamaService
from app.services.meta_rag_service import MetaRAGService
from app.services.gw2_data_store import GW2DataStore


class TeamStrategyAgent:
    """High-level strategist used by TeamCommanderAgent.

    V1: minimal implementation that prepares a rich prompt and
    delegates composition to the LLM, returning a parsed
    TeamStrategyPlan. If anything fails, the caller should
    fall back to rule-based logic.
    """

    def __init__(
        self,
        meta_rag: Optional[MetaRAGService] = None,
        ollama_service: Optional[OllamaService] = None,
    ) -> None:
        self.meta_rag = meta_rag or MetaRAGService()
        self._ollama = ollama_service or OllamaService()
        self._data_store = GW2DataStore()

    def _build_profession_spec_vocab_fragment(self) -> str:
        """Construit dynamiquement le vocabulaire professions/spécialisations.

        Utilise les dumps GW2 (professions.json, specializations.json) pour
        toujours refléter les élites actuelles (y compris de futures extensions).

        En cas d'erreur ou de données manquantes, on retombe sur la liste
        statique précédente pour garder un comportement robuste.
        """

        try:
            professions = self._data_store.get_professions()
            specializations = self._data_store.get_specializations()
        except Exception:
            # Fallback: liste codée en dur (EoD)
            return (
                "- Champ 'profession' : doit être EXACTEMENT l'une des valeurs suivantes :\n"
                "  Guardian, Warrior, Engineer, Ranger, Thief, Elementalist, Mesmer, Necromancer, Revenant.\n"
                "- Champ 'specialization' : doit être une spécialisation associée à la profession :\n"
                "  Guardian : Dragonhunter, Firebrand, Willbender.\n"
                "  Warrior : Berserker, Spellbreaker, Bladesworn.\n"
                "  Engineer : Scrapper, Holosmith, Mechanist.\n"
                "  Ranger : Druid, Soulbeast, Untamed.\n"
                "  Thief : Daredevil, Deadeye, Specter.\n"
                "  Elementalist : Tempest, Weaver, Catalyst.\n"
                "  Mesmer : Chronomancer, Mirage, Virtuoso.\n"
                "  Necromancer : Reaper, Scourge, Harbinger.\n"
                "  Revenant : Herald, Renegade, Vindicator.\n"
            )

        prof_names = []
        for p in professions or []:
            name = p.get("name")
            if isinstance(name, str) and name:
                prof_names.append(name)

        prof_names = sorted(set(prof_names))

        # Construire le mapping profession -> liste de spécialisations
        mapping: Dict[str, set[str]] = {}
        for spec in specializations or []:
            spec_name = spec.get("name")
            spec_prof = spec.get("profession")
            if not (isinstance(spec_name, str) and spec_name):
                continue
            if not (isinstance(spec_prof, str) and spec_prof):
                continue
            mapping.setdefault(spec_prof, set()).add(spec_name)

        lines = []
        lines.append("- Champ 'profession' : doit être EXACTEMENT l'une des valeurs suivantes :\n")
        if prof_names:
            lines.append("  " + ", ".join(prof_names) + ".\n")
        else:
            lines.append(
                "  Guardian, Warrior, Engineer, Ranger, Thief, Elementalist, Mesmer, Necromancer, Revenant.\n"
            )

        lines.append("- Champ 'specialization' : doit être une spécialisation associée à la profession :\n")
        if mapping:
            for prof in sorted(mapping.keys()):
                specs_sorted = sorted(mapping[prof])
                lines.append(f"  {prof} : " + ", ".join(specs_sorted) + ".\n")
        else:
            # Fallback si aucune spé n'est trouvée
            lines.append(
                "  Guardian : Dragonhunter, Firebrand, Willbender.\n"
                "  Warrior : Berserker, Spellbreaker, Bladesworn.\n"
                "  Engineer : Scrapper, Holosmith, Mechanist.\n"
                "  Ranger : Druid, Soulbeast, Untamed.\n"
                "  Thief : Daredevil, Deadeye, Specter.\n"
                "  Elementalist : Tempest, Weaver, Catalyst.\n"
                "  Mesmer : Chronomancer, Mirage, Virtuoso.\n"
                "  Necromancer : Reaper, Scourge, Harbinger.\n"
                "  Revenant : Herald, Renegade, Vindicator.\n"
            )

        return "".join(lines)

    def _infer_mode(self, message: str, explicit_mode: Optional[str]) -> str:
        if explicit_mode:
            return explicit_mode.lower()
        m = message.lower()
        if "roam" in m or "roaming" in m:
            return "wvw_roam"
        if "outnumber" in m or "out-number" in m:
            return "wvw_outnumber"
        if "havoc" in m:
            return "wvw_havoc"
        return "wvw_zerg"

    def _infer_experience(self, message: str, explicit_experience: Optional[str]) -> str:
        if explicit_experience:
            return explicit_experience.lower()
        m = message.lower()
        if any(k in m for k in ["debutant", "débutant", "beginner"]):
            return "beginner"
        if "expert" in m:
            return "expert"
        return "intermediate"

    def _infer_team_size(self, message: str) -> int:
        m = message.lower()
        match = re.search(r"(\d+)\s+groupes?\s+de\s+(\d+)", m)
        if match:
            groups = int(match.group(1))
            slots_per_group = int(match.group(2))
            return max(1, min(groups * slots_per_group, 50))

        match = re.search(r"\b(?:équipe|team|squad)\s+de\s+(\d+)", m)
        if match:
            return max(1, min(int(match.group(1)), 50))

        match = re.search(r"\b(\d+)\s+joueurs?", m)
        if match:
            return max(1, min(int(match.group(1)), 50))

        return 5

    def _build_system_prompt(self) -> str:
        vocab_fragment = self._build_profession_spec_vocab_fragment()
        return (
            "Tu es un stratège Guild Wars 2 spécialisé en WvW. "
            "Ton rôle est de concevoir des compositions d'équipe complètes "
            "(professions, spécialisations, rôles précis) pour un Commandant humain.\n\n"
            "Principes généraux :\n"
            "- Pour du roaming : privilégier mobilité, burst et autosuffisance défensive.\n"
            "- Pour du zerg : privilégier stabilité, boon share, sustain et boon strip.\n"
            "- Pour du havoc / outnumber : composition hybride entre roaming et zerg (burst + sustain de groupe).\n\n"
            "Tu t'inspires de la méta décrite dans le contexte fourni, "
            "mais tu peux proposer des variantes crédibles.\n\n"
            "Vocabulaire GW2 STRICT à utiliser :\n"
            f"{vocab_fragment}"
            "- Champ 'weapon_preference' : doit contenir UNIQUEMENT une arme (pas une spécialisation),\n"
            "  par ex. 'Hammer', 'Rifle', 'Staff', 'Greatsword', 'Longbow', 'Shortbow', 'Sword', 'Dagger',\n"
            "  'Pistol', 'Axe', 'Mace', 'Scepter', 'Focus', 'Torch', 'Shield', 'Warhorn'.\n"
            "  Exemple : pour un 'Scrapper marteau', renvoie profession='Engineer', specialization='Scrapper',\n"
            "  weapon_preference='Hammer'. Ne mets JAMAIS 'Hammer' dans 'specialization'.\n\n"
            "Contraintes strictes :\n"
            "- La réponse DOIT être un JSON valide décrivant une stratégie de team.\n"
            "- Utilise le champ 'weapon_preference' pour indiquer l'arme principale de chaque slot,\n"
            "  et n'utilise JAMAIS une arme dans 'profession' ou 'specialization'.\n"
            "- Les rôles doivent être des étiquettes courtes : 'dps', 'support', 'heal', 'boon', 'strip', 'tank', etc.\n"
        )

    async def propose_strategy(self, request: TeamStrategyRequest) -> TeamStrategyPlan:
        """Propose a high-level strategy plan using LLM + MetaRAG.

        This V1 implementation intentionally keeps parsing simple and
        lets the model decide the exact composition shape.
        """

        mode = self._infer_mode(request.message, request.explicit_mode)
        experience = self._infer_experience(request.message, request.explicit_experience)
        team_size = self._infer_team_size(request.message)

        # Rough mapping from internal mode to a generic game_mode label for MetaRAG
        if "wvw" in mode:
            game_mode = "wvw_zerg" if "zerg" in mode else "wvw"
        else:
            game_mode = "wvw"

        meta_context: Optional[str] = None
        try:
            meta_context = self.meta_rag.build_context_for_build(
                game_mode=game_mode,
                profession=None,
                specialization=None,
                role=None,
                question=request.message,
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("MetaRAGService in TeamStrategyAgent failed", extra={"error": str(e)})
            meta_context = None

        system_prompt = self._build_system_prompt()

        user_prompt_parts = [
            f"Demande utilisateur: {request.message}",
            f"Mode déduit: {mode}",
            f"Niveau d'expérience: {experience}",
            f"Taille d'équipe estimée: {team_size}",
        ]

        if request.constraints:
            try:
                constraints_json = json.dumps(request.constraints, ensure_ascii=False)
            except Exception:
                constraints_json = str(request.constraints)
            user_prompt_parts.append(f"Contraintes JSON: {constraints_json}")

        if meta_context:
            user_prompt_parts.append("\nContexte méta (extraits de builds/meta guides):\n" + meta_context)

        # Example of expected JSON structure (loose, validated afterwards)
        user_prompt_parts.append(
            "\nRéponds UNIQUEMENT avec un objet JSON. Exemple simplifié de structure attendue (à adapter):\n"
            "{"
            "\"mode\": \"wvw_roam\","  # mode de jeu déduit ou confirmé\n"
            "\"team_size\": 3,"  # nombre total de joueurs\n"
            "\"groups\": ["
            "  {\"index\": 1, \"label\": \"Groupe principal\", \"slots\": ["
            "    {\"index\": 0, \"group_index\": 1, \"role\": \"support\", "
            "\"profession\": \"Guardian\", \"specialization\": \"Firebrand\", "
            "\"weapon_preference\": \"Staff\", \"playstyle\": \"bunker support\"},"
            "    {\"index\": 1, \"group_index\": 1, \"role\": \"dps\", "
            "\"profession\": \"Necromancer\", \"specialization\": \"Harbinger\", "
            "\"weapon_preference\": \"Pistol\"}"
            "  ]}"
            "] ,"
            "\"global_concept\": \"Roaming burst + 1 support peel\","
            "\"high_level_notes\": [\"Focus sur la mobilité et le burst en petit comité\"]"
            "}"
        )

        prompt = "\n\n".join(user_prompt_parts)

        # Let OllamaService handle the JSON parsing via generate_structured
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "mode": {"type": "string"},
                "team_size": {"type": "integer"},
                "groups": {"type": "array"},
                "global_concept": {"type": ["string", "null"]},
                "high_level_notes": {"type": "array"},
            },
            "required": ["mode", "team_size", "groups"],
            "additionalProperties": True,
        }

        logger.info("Running TeamStrategyAgent with Ollama")
        raw: Dict[str, Any] = await self._ollama.generate_structured(
            prompt=prompt,
            system_prompt=system_prompt,
            schema=schema,
            max_tokens=1024,
        )

        try:
            plan = TeamStrategyPlan(**raw)
        except Exception as e:
            logger.error("Failed to validate TeamStrategyPlan from LLM", extra={"error": str(e), "raw": raw})
            raise

        # Clamp values defensively
        plan.team_size = max(1, min(plan.team_size or team_size, 50))
        if not plan.mode:
            plan.mode = mode

        return plan

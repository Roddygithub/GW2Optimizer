from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import logger
from app.services.gw2_api_client import GW2APIClient


BUILD_TEMPLATE_TYPE = 0x0D

# Mapping from build template profession codes to GW2 profession IDs
_PROFESSION_CODE_MAP: Dict[int, str] = {
    1: "Guardian",
    2: "Warrior",
    3: "Engineer",
    4: "Ranger",
    5: "Thief",
    6: "Elementalist",
    7: "Mesmer",
    8: "Necromancer",
    9: "Revenant",
}


class ChatCodeDecoder:
    """Decode GW2 build template chat codes into API-ready IDs.

    This decoder focuses on link type 0x0D (build template) and returns a
    structure directly exploitable by BuildAnalysisService::

        {
          "profession_code": int,
          "specialization_id": int | None,
          "trait_ids": List[int],
          "skill_ids": List[int],
        }
    """

    def __init__(self, gw2_client: Optional[GW2APIClient] = None) -> None:
        self.gw2_client = gw2_client or GW2APIClient()

    # ------------------------------------------------------------------
    # Low-level binary decoding
    # ------------------------------------------------------------------
    def _decode_raw(self, code: str) -> Tuple[int, List[int], List[List[int]], List[int]]:
        """Return (profession_code, specialization_ids, trait_choices, palette_ids)."""

        if not code:
            raise ValueError("Empty chat code")

        text = code.strip()
        if text.startswith("[&") and text.endswith("]"):
            inner = text[2:-1]
        else:
            inner = text

        try:
            raw = base64.b64decode(inner)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid base64 chat code: {exc}") from exc

        if len(raw) < 2:
            raise ValueError("Chat code payload too short")

        if raw[0] != BUILD_TEMPLATE_TYPE:
            raise ValueError(f"Unsupported chat code type: 0x{raw[0]:02X}")

        # Profession code (1..9)
        offset = 1
        profession_code = int(raw[offset])
        offset += 1

        # Three specialization lines: (spec_id, trait-byte)
        specialization_ids: List[int] = []
        trait_choices: List[List[int]] = []

        for _ in range(3):
            if offset + 2 > len(raw):
                specialization_ids.append(0)
                trait_choices.append([0, 0, 0])
                continue

            spec_id = int(raw[offset])
            traits_byte = int(raw[offset + 1])
            offset += 2

            # Traits byte packs 3 two-bit choices in reverse order
            # Bits (b7..b0): [x x t3_hi t3_lo t2_hi t2_lo t1_hi t1_lo]
            first = traits_byte & 0b11
            second = (traits_byte >> 2) & 0b11
            third = (traits_byte >> 4) & 0b11

            specialization_ids.append(spec_id)
            trait_choices.append([first, second, third])

        # Ten 16-bit little-endian palette IDs (heal/utility/elite x land/water)
        palette_ids: List[int] = []
        for _ in range(10):
            if offset + 2 > len(raw):
                break
            low = raw[offset]
            high = raw[offset + 1]
            offset += 2
            palette_ids.append(int(low | (high << 8)))

        logger.debug(
            "Decoded raw chat code",
            extra={
                "profession_code": profession_code,
                "specialization_ids": specialization_ids,
                "trait_choices": trait_choices,
                "palette_ids": palette_ids,
            },
        )

        return profession_code, specialization_ids, trait_choices, palette_ids

    # ------------------------------------------------------------------
    # High-level decoding to specialization/trait/skill IDs
    # ------------------------------------------------------------------
    async def _resolve_traits(
        self, specialization_ids: List[int], trait_choices: List[List[int]]
    ) -> Tuple[Optional[int], List[int]]:
        """Resolve trait IDs from spec IDs + trait choices.

        Returns (primary_specialization_id, trait_ids).
        The primary specialization prefers an elite spec if present.
        """

        trait_ids: List[int] = []
        primary_spec_id: Optional[int] = None

        for index, spec_id in enumerate(specialization_ids):
            if not spec_id:
                continue

            spec_data = await self.gw2_client.get_specialization_details(spec_id)
            if not spec_data:
                continue

            is_elite = bool(spec_data.get("elite"))
            if primary_spec_id is None or is_elite:
                primary_spec_id = spec_id

            major_traits = spec_data.get("major_traits") or []
            choices = trait_choices[index] if index < len(trait_choices) else []

            for tier_index, choice in enumerate(choices):
                # 1..3 => top/middle/bottom. 0 means no trait selected.
                if choice not in (1, 2, 3):
                    continue
                major_index = tier_index * 3 + (choice - 1)
                if 0 <= major_index < len(major_traits):
                    tid = major_traits[major_index]
                    if isinstance(tid, int):
                        trait_ids.append(tid)

        # Deduplicate while preserving order
        seen: set[int] = set()
        unique: List[int] = []
        for tid in trait_ids:
            if tid not in seen:
                seen.add(tid)
                unique.append(tid)

        return primary_spec_id, unique

    async def _resolve_skills(self, profession_code: int, palette_ids: List[int]) -> List[int]:
        """Resolve palette IDs to GW2 skill IDs via /v2/professions (v=latest)."""

        profession_name = _PROFESSION_CODE_MAP.get(profession_code)
        if not profession_name:
            logger.warning("Unknown profession code in chat code", extra={"profession_code": profession_code})
            return []

        try:
            data = await self.gw2_client.get_profession_with_skills(profession_name)
        except Exception as exc:  # pragma: no cover - network failures
            logger.error(
                "Failed to fetch profession for palette resolution",
                extra={"profession": profession_name, "error": str(exc)},
            )
            return []

        raw_mapping = data.get("skills_by_palette") or {}

        # Normalize skills_by_palette into a dict[int, Any]
        palette_map: Dict[int, Any] = {}
        if isinstance(raw_mapping, dict):
            for key, value in raw_mapping.items():
                try:
                    pid = int(key)
                except (TypeError, ValueError):
                    continue
                palette_map[pid] = value
        elif isinstance(raw_mapping, list):
            # Format observed from GW2 API: [[palette_id, skill_id], ...]
            for entry in raw_mapping:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    pid, sid = entry[0], entry[1]
                    if isinstance(pid, int):
                        palette_map[pid] = sid
                elif isinstance(entry, dict):
                    pid = entry.get("palette_id")
                    if not isinstance(pid, int):
                        continue
                    palette_map[pid] = entry

        skill_ids: List[int] = []

        for pid in palette_ids:
            if not pid:
                continue
            entry = palette_map.get(pid)
            if entry is None:
                continue

            sid: Optional[int] = None
            if isinstance(entry, int):
                sid = entry
            elif isinstance(entry, dict):
                value = entry.get("id") or entry.get("skill_id")
                if isinstance(value, int):
                    sid = value

            if isinstance(sid, int):
                skill_ids.append(sid)

        # Deduplicate while preserving order
        seen: set[int] = set()
        unique_skills: List[int] = []
        for sid in skill_ids:
            if sid not in seen:
                seen.add(sid)
                unique_skills.append(sid)

        return unique_skills

    async def decode_build(self, code: str) -> Dict[str, Any]:
        """Decode a chat code into specialization_id, trait_ids and skill_ids."""

        profession_code, spec_ids, trait_choices, palette_ids = self._decode_raw(code)
        primary_spec_id, trait_ids = await self._resolve_traits(spec_ids, trait_choices)
        skill_ids = await self._resolve_skills(profession_code, palette_ids)

        result: Dict[str, Any] = {
            "profession_code": profession_code,
            "specialization_id": primary_spec_id,
            "trait_ids": trait_ids,
            "skill_ids": skill_ids,
        }

        logger.info(
            "Decoded build chat code",
            extra={
                "profession_code": profession_code,
                "specialization_id": primary_spec_id,
                "n_traits": len(trait_ids),
                "n_skills": len(skill_ids),
            },
        )

        return result


async def decode_chat_code(code: str) -> Dict[str, Any]:
    """Convenience wrapper to decode a build chat code in one call."""

    decoder = ChatCodeDecoder()
    return await decoder.decode_build(code)

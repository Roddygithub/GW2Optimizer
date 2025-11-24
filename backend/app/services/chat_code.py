from __future__ import annotations

import base64
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from app.core.logging import logger


@dataclass
class DecodedChatCode:
    """Intermediate representation of a GW2 build chat code.

    This structure is intentionally low-level and close to the raw format:
    - profession_code: numeric profession code (1..9).
    - specialization_ids: up to 3 specialization IDs (0 means unused).
    - trait_choices: for each specialization, 3 two-bit choices (0..3).
    - skill_palette_ids: 10 palette IDs (may include zeros for empty slots).
    """

    profession_code: int
    specialization_ids: List[int]
    trait_choices: List[List[int]]
    skill_palette_ids: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ChatCodeDecoder:
    """Decoder for GW2 build template chat codes.

    Only the build template link type (0x0D) is supported. The decoder does
    *not* hit the GW2 API; it only exposes specialization IDs, trait choices
    and skill palette IDs so that higher-level services can resolve them.
    """

    BUILD_TEMPLATE_TYPE = 0x0D

    @classmethod
    def decode_chat_code(cls, code: str) -> DecodedChatCode:
        """Decode a GW2 build template chat code.

        Args:
            code: Chat code string, e.g. "[&DQg1OSc5AjkAAAAAmQEAAJkBAAAAAJkBAAAA...]".

        Returns:
            DecodedChatCode with profession code, specialization IDs,
            per-line trait choices and skill palette IDs.

        Raises:
            ValueError: If the code is invalid or not a build template.
        """

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

        if raw[0] != cls.BUILD_TEMPLATE_TYPE:
            raise ValueError(f"Unsupported chat code type: 0x{raw[0]:02X}")

        # === Profession code ===
        offset = 1
        profession_code = int(raw[offset])
        offset += 1

        # === 3 specializations (id + trait choices byte) ===
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

            # 3 two-bit choices stored in reverse order, lowest bits first.
            # Bits layout (b7..b0): [unused, unused, t3_hi, t3_lo, t2_hi, t2_lo, t1_hi, t1_lo]
            first_choice = traits_byte & 0b11
            second_choice = (traits_byte >> 2) & 0b11
            third_choice = (traits_byte >> 4) & 0b11

            specialization_ids.append(spec_id)
            trait_choices.append([first_choice, second_choice, third_choice])

        # === 10 skill palette IDs (16-bit little-endian) ===
        skill_palette_ids: List[int] = []
        for _ in range(10):
            if offset + 2 > len(raw):
                break
            low = raw[offset]
            high = raw[offset + 1]
            offset += 2
            palette_id = int(low | (high << 8))
            skill_palette_ids.append(palette_id)

        logger.debug(
            "Decoded chat code",
            extra={
                "profession_code": profession_code,
                "specialization_ids": specialization_ids,
                "trait_choices": trait_choices,
                "skill_palette_ids": skill_palette_ids,
            },
        )

        return DecodedChatCode(
            profession_code=profession_code,
            specialization_ids=specialization_ids,
            trait_choices=trait_choices,
            skill_palette_ids=skill_palette_ids,
        )


def decode_chat_code(code: str) -> Dict[str, Any]:
    """Convenience wrapper returning a plain dict for JSON friendliness."""

    decoded = ChatCodeDecoder.decode_chat_code(code)
    return decoded.to_dict()

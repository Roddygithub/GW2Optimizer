from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.services.meta_build_catalog import MetaBuild, list_meta_builds, query_meta_builds


class MetaRAGService:
    """Lightweight in-memory RAG service over meta builds.

    This service works on top of the existing meta_build_catalog registry and
    provides:
      - simple lexical retrieval of relevant meta builds for a given build
      - compact text snippets suitable for inclusion in LLM prompts
    """

    def __init__(self, default_max_chars: int = 800) -> None:
        self.default_max_chars = default_max_chars

    def retrieve_for_build(
        self,
        *,
        game_mode: str = "wvw",
        profession: Optional[str] = None,
        specialization: Optional[str] = None,
        role: Optional[str] = None,
        question: Optional[str] = None,
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve top-k meta builds relevant for the given build profile.

        This is a lexical / filter-based retrieval over the in-memory
        META_BUILD_REGISTRY. It first tries strict filters (profession,
        specialization, role, game_mode), then falls back progressively if
        nothing is found.
        """

        # 1) Try strict filter
        candidates: List[MetaBuild] = query_meta_builds(
            profession=profession,
            specialization=specialization,
            role=role,
            game_mode=game_mode,
        )

        # 2) If nothing, relax to game_mode only
        if not candidates:
            candidates = query_meta_builds(game_mode=game_mode)

        # 3) If still nothing, use all registered meta builds
        if not candidates:
            candidates = list_meta_builds()

        if not candidates:
            return []

        scored: List[Dict[str, Any]] = []
        for mb in candidates:
            score = self._score_meta_build(
                meta=mb,
                profession=profession,
                specialization=specialization,
                role=role,
                question=question,
            )
            scored.append({"score": score, "meta": mb})

        # Sort by score desc, then by name for stability
        scored.sort(key=lambda x: (x["score"], x["meta"].name.lower()), reverse=True)

        results: List[Dict[str, Any]] = []
        for entry in scored[: max_results or 3]:
            mb: MetaBuild = entry["meta"]
            snippet = self._build_snippet(mb)
            results.append(
                {
                    "id": mb.id,
                    "name": mb.name,
                    "profession": mb.profession,
                    "specialization": mb.specialization,
                    "role": mb.role,
                    "game_mode": mb.game_mode,
                    "source": mb.source,
                    "tags": list(mb.tags),
                    "snippet": snippet,
                    "score": entry["score"],
                }
            )

        return results

    def build_context_for_build(
        self,
        *,
        game_mode: str = "wvw",
        profession: Optional[str] = None,
        specialization: Optional[str] = None,
        role: Optional[str] = None,
        question: Optional[str] = None,
        max_results: int = 3,
        max_chars: Optional[int] = None,
    ) -> Optional[str]:
        """Build a compact textual context for LLM prompts based on meta builds.

        Returns a multi-line string mentioning a few external meta builds and
        their key characteristics (source, role, stats, runes), or None if no
        relevant build is found.
        """

        try:
            hits = self.retrieve_for_build(
                game_mode=game_mode,
                profession=profession,
                specialization=specialization,
                role=role,
                question=question,
                max_results=max_results,
            )
        except Exception as e:  # pragma: no cover - defensive guardrail
            logger.warning("MetaRAGService.retrieve_for_build failed", extra={"error": str(e)})
            return None

        if not hits:
            return None

        lines: List[str] = []
        lines.append("Meta RAG context (external guides and meta builds):")
        for h in hits:
            source = h.get("source") or "external"
            name = h.get("name") or "Unknown build"
            spec = h.get("specialization") or "Unknown spec"
            role_label = h.get("role") or "unknown role"
            snippet = h.get("snippet") or ""
            lines.append(f"- [{source}] {name} ({spec} {role_label}) :: {snippet}")

        text = "\n".join(lines)
        limit = max_chars or self.default_max_chars
        return text[:limit]

    def _score_meta_build(
        self,
        *,
        meta: MetaBuild,
        profession: Optional[str],
        specialization: Optional[str],
        role: Optional[str],
        question: Optional[str],
    ) -> float:
        """Heuristic scoring for a meta build.

        Higher score means more relevant. This is intentionally simple and
        fully in-memory.
        """

        score = 0.0

        if profession and meta.profession.lower() == profession.lower():
            score += 4.0
        if specialization and meta.specialization.lower() == specialization.lower():
            score += 3.0
        if role and meta.role.lower() == role.lower():
            score += 2.0

        # Lightweight lexical bonus based on the question / context
        if question:
            q = question.lower()
            text_parts: List[str] = []
            if meta.notes:
                text_parts.append(meta.notes)
            if meta.stats_text:
                text_parts.append(meta.stats_text)
            if meta.runes_text:
                text_parts.append(meta.runes_text)
            if meta.tags:
                text_parts.append(" ".join(meta.tags))
            haystack = " ".join(text_parts).lower()

            if haystack:
                tokens = [t for t in q.split() if len(t) >= 3]
                for tok in tokens:
                    if tok in haystack:
                        score += 0.5

        return score

    def _build_snippet(self, meta: MetaBuild) -> str:
        """Build a short human-readable snippet for a meta build."""

        parts: List[str] = []

        header = f"Meta build: {meta.name} ({meta.specialization} {meta.role})"
        if meta.source:
            header += f" [source: {meta.source}]"
        parts.append(header)

        if meta.stats_text:
            parts.append(f"Stats: {meta.stats_text}")
        if meta.runes_text:
            parts.append(f"Runes: {meta.runes_text}")
        if meta.notes:
            parts.append(f"Notes: {meta.notes}")

        snippet = " | ".join(parts)
        # Hard cap to avoid blowing up prompts even if data is long
        return snippet[:400]


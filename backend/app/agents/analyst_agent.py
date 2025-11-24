import json
import re
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.services.ai.ollama_service import OllamaService


class AnalystAgent(BaseAgent):
    def __init__(self, ollama_service: Optional[OllamaService] = None) -> None:
        super().__init__(
            name="AnalystAgent",
            description="Analyse de compétences et de builds Guild Wars 2 pour le WvW.",
            version="1.1.0",
            capabilities=["skill_analysis", "build_synergy", "wvw_evaluation"],
        )
        self._ollama = ollama_service or OllamaService()

    async def _initialize_impl(self) -> None:
        return None

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        context = inputs.get("context", "WvW Zerg")

        # ==================== Build synergy mode ====================
        if "build_data" in inputs:
            build_data = inputs["build_data"]

            system_prompt = (
                "Tu es un expert theorycrafter Guild Wars 2 spécialisé en WvW. "
                "On va te donner un build partiel au format JSON (spécialisation, traits, skills) dérivé de l'API GW2, "
                "avec éventuellement un champ 'equipment_summary' décrivant l'équipement (par ex. stats_text, runes_text) "
                "et des champs numériques d'estimation de dégâts (par ex. 'estimated_damage_berserker' sur certains skills, calculés pour un profil Berserker avec Power=2500 et une arme de force moyenne).\n\n"
                "Ta tâche est d'analyser la SYNERGIE globale du build pour le contexte indiqué.\n\n"
                "Contraintes strictes :\n"
                "- Baser ton analyse UNIQUEMENT sur les champs fournis dans build_data (specialization, traits, skills et leurs champs, equipment_summary éventuel, champs d'estimation de dégâts, etc.).\n"
                "- Si un champ 'equipment_summary' est présent dans build_data, utilise-le pour affiner ton jugement sur le rôle, les statistiques et les runes du build, sans inventer d'éléments absents.\n"
                "- Si des champs d'estimation de dégâts (par ex. 'estimated_damage_berserker') sont présents sur les skills, utilise-les pour juger le burst et comparer les options de dégâts bruts, sans inventer de nouveaux nombres.\n"
                "- Ne pas inventer d'effets, de boons ou de conditions qui ne sont pas présents dans ces données.\n"
                "- Quand tu cites un boon ou une altération, utiliser exactement le nom présent dans les descriptions ou facts.\n"
                "- La sortie DOIT être un objet JSON strictement valide, sans texte supplémentaire, sans markdown.\n"
                '- IMPORTANT : N\'utilise JAMAIS de guillemets doubles (") à l\'intérieur des textes JSON. Utilise des apostrophes (\') à la place.\n'
                "- Sois concis dans strengths, weaknesses et summary. Pas de markdown, pas de listes à puces. Tu peux mentionner explicitement les estimations de dégâts quand c'est pertinent pour justifier le score."
            )

            build_json = json.dumps(build_data, ensure_ascii=False, indent=2)
            prompt = (
                f"Contexte: {context}\n\n"
                "Build au format JSON (build_data):\n"
                f"{build_json}\n\n"
                "Réponds avec un objet JSON de la forme EXACTE suivante (sans commentaire ni texte autour) :\n"
                "{"
                '"synergy_score": "S|A|B|C",'
                '"strengths": ["..."],'
                '"weaknesses": ["..."],'
                '"summary": "Texte explicatif court basé UNIQUEMENT sur les champs de build_data"'
                "}"
            )

            schema: Dict[str, Any] = {
                "type": "object",
                "properties": {
                    "synergy_score": {
                        "type": "string",
                        "enum": ["S", "A", "B", "C"],
                    },
                    "strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "weaknesses": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "summary": {"type": "string"},
                },
                "required": ["synergy_score", "strengths", "weaknesses", "summary"],
                "additionalProperties": True,
            }

            logger.info("Running build synergy analysis with AnalystAgent (Ollama)")
            ai_result: Any = {}
            for attempt in range(2):
                try:
                    ai_result = await self._ollama.generate_structured(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        schema=schema,
                    )
                    break
                except ValueError as e:
                    if attempt == 0:
                        logger.warning(
                            "Structured JSON for build analysis was invalid, retrying once..."
                        )
                        continue
                    logger.warning(
                        "Structured JSON for build analysis still invalid after retry, "
                        "falling back to line protocol. Error: %s",
                        e,
                    )
                    return await self._run_build_fallback(build_data=build_data, context=context)

            synergy_score: Optional[str] = None
            strengths: Any = None
            weaknesses: Any = None
            summary: Optional[str] = None

            if isinstance(ai_result, dict):
                synergy_score = ai_result.get("synergy_score")
                # Nettoyage défensif : si le modèle a renvoyé une chaîne complexe
                # (par ex. "S|A|B|C"), on ne garde qu'une seule lettre valide.
                if isinstance(synergy_score, str) and ("|" in synergy_score or len(synergy_score) > 2):
                    match = re.search(r"[SABC]", synergy_score.upper())
                    synergy_score = match.group(0) if match else "B"

                strengths = ai_result.get("strengths")
                weaknesses = ai_result.get("weaknesses")
                summary = ai_result.get("summary")

            return {
                "context": context,
                "synergy_score": synergy_score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "summary": summary,
                "raw_response": ai_result,
                "build_data": build_data,
            }

        # ==================== Skill analysis mode ====================
        skill_data = inputs["skill_data"]

        system_prompt = (
            "Tu es un expert de Guild Wars 2 WvW. On va te donner le JSON brut d'une compétence "
            "tel que renvoyé par l'API officielle Guild Wars 2 (skill_data). "
            "Tu dois dire si cette compétence est Méta, Viable ou Inutile pour le mode de jeu indiqué, et pourquoi.\n\n"
            "Contraintes strictes :\n"
            "- Baser ton analyse UNIQUEMENT sur les champs fournis dans skill_data (par ex. name, description, facts, "
            "traited_facts, flags, etc.).\n"
            "- Ne pas inventer d'effets, de boons ou de conditions qui ne sont pas présents dans ces données.\n"
            "- Quand tu cites un boon ou une altération, utiliser exactement le nom présent dans la description ou les facts, "
            "sans le renommer (par ex. ne pas confondre Résolution et Résistance).\n"
            "- La sortie DOIT être un objet JSON strictement valide, sans texte supplémentaire, sans markdown.\n"
            "- Si tu dois utiliser des guillemets dans une chaîne JSON, échappe-les avec \\\"."
        )
        skill_json = json.dumps(skill_data, ensure_ascii=False, indent=2)
        prompt = (
            f"Contexte: {context}\n\n"
            "Données du skill au format JSON (skill_data):\n"
            f"{skill_json}\n\n"
            "Réponds avec un objet JSON de la forme EXACTE suivante (sans commentaire ni texte autour) :\n"
            "{"
            '"rating": "Méta|Viable|Inutile",'
            '"reason": "Texte explicatif court basé UNIQUEMENT sur les champs de skill_data",'
            '"tags": ["support", "zerg", "autres"]'
            "}"
        )

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "rating": {
                    "type": "string",
                    "enum": ["Méta", "Viable", "Inutile"],
                },
                "reason": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["rating", "reason", "tags"],
            "additionalProperties": True,
        }

        logger.info("Running skill analysis with AnalystAgent (Ollama)")
        ai_result = await self._ollama.generate_structured(
            prompt=prompt,
            system_prompt=system_prompt,
            schema=schema,
        )

        rating: Optional[str] = None
        reason: Optional[str] = None
        tags: Optional[Any] = None

        if isinstance(ai_result, dict):
            rating = ai_result.get("rating")
            reason = ai_result.get("reason")
            tags = ai_result.get("tags")

        return {
            "skill_id": skill_data.get("id"),
            "skill_name": skill_data.get("name"),
            "context": context,
            "rating": rating,
            "reason": reason,
            "tags": tags,
            "raw_response": ai_result,
        }

    async def _run_build_fallback(self, build_data: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Fallback texte structuré pour l'analyse de build.

        Format de sortie attendu (UNE SEULE LIGNE, sans markdown) :
        synergy_score | strengths | weaknesses | summary

        - synergy_score: une lettre parmi S, A, B, C
        - strengths: liste de points forts séparés par ';'
        - weaknesses: liste de faiblesses séparées par ';'
        - summary: phrase courte sans '|' ni ';'
        """

        system_prompt = (
            "Tu es un expert theorycrafter Guild Wars 2 spécialisé en WvW. "
            "On va te donner un build partiel au format JSON (spécialisation, traits, skills) dérivé de l'API GW2.\n\n"
            "Ta tâche est d'analyser la SYNERGIE globale du build pour le contexte indiqué.\n\n"
            "IMPORTANT : cette fois-ci, tu dois répondre dans un format TEXTE SIMPLIFIÉ, PAS en JSON.\n"
            "Format EXACT attendu (une seule ligne, sans guillemets autour) :\n"
            "synergy_score | strengths | weaknesses | summary\n\n"
            "Règles supplémentaires :\n"
            "- synergy_score DOIT être UNE SEULE lettre : S, A, B ou C (ne réponds pas 'S|A|B|C').\n"
            "- strengths est une liste de points forts séparés par ';' (sans point-virgule dans chaque élément).\n"
            "- weaknesses est une liste de faiblesses séparées par ';' (sans point-virgule dans chaque élément).\n"
            "- summary est une phrase courte qui ne contient NI '|' NI ';'.\n"
            "- N'utilise JAMAIS de markdown. Pas de liste à puces. Une seule ligne de sortie."
        )

        build_json = json.dumps(build_data, ensure_ascii=False, indent=2)
        prompt = (
            f"Contexte: {context}\n\n"
            "Build au format JSON (build_data):\n"
            f"{build_json}\n\n"
            "Réponds strictement avec une seule ligne au format décrit ci-dessus, sans guillemets.")

        raw_text = await self._ollama.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=256,
        )

        # Supporter les réponses multi-lignes : on cherche la dernière ligne non vide
        # qui ressemble à une ligne de données (au moins 2 séparateurs '|').
        stripped = raw_text.strip()
        lines = [l.strip() for l in stripped.splitlines() if l.strip()] if stripped else []
        selected_index: int | None = None
        if lines:
            # Indices des lignes candidates (>= 2 séparateurs '|')
            candidate_indices = [i for i, l in enumerate(lines) if l.count("|") >= 2]
            if candidate_indices:
                selected_index = candidate_indices[-1]
            else:
                selected_index = len(lines) - 1
            line = lines[selected_index]
        else:
            line = ""
            selected_index = None
        parts = [p.strip() for p in line.split("|")]
        if not parts or len(parts) < 2:
            raise ValueError(f"Invalid fallback line format: '{line}'")

        # On filtre d'abord tous les segments qui ressemblent à des labels
        # (synergy_score, strengths, weaknesses, summary, etc.),
        # puis on mappe les valeurs restantes dans l'ordre :
        #   synergy_score, strengths, weaknesses, summary.
        label_keywords = ("synergy", "score", "strength", "force", "weak", "faiblesse", "summary", "résumé")
        values = [p for p in parts if p and not any(k in p.lower() for k in label_keywords)]

        if not values:
            # Le modèle a probablement renvoyé uniquement la ligne d'en-tête.
            # On évite de planter et on retourne un résultat neutre.
            logger.warning(
                "Build fallback returned only header/labels, returning neutral result.",
                extra={"line": line},
            )
            return {
                "context": context,
                "synergy_score": "B",
                "strengths": None,
                "weaknesses": None,
                "summary": None,
                "raw_response": {"fallback_raw": raw_text},
                "build_data": build_data,
            }

        synergy_score: Optional[str] = values[0] if values else None
        # Nettoyage ultime du score si le modèle a renvoyé une chaîne complexe
        if synergy_score and ("|" in synergy_score or len(synergy_score) > 2):
            # Exemple : "S|A|B|C" ou "Score: A" -> on extrait la première lettre valide
            match = re.search(r"[SABC]", synergy_score.upper())
            synergy_score = match.group(0) if match else "B"
        strengths_raw: str | None = None
        weaknesses_raw: str | None = None
        summary: Optional[str] = None

        if len(values) == 2:
            # Cas minimaliste : "S | Résumé court" (pas de listes forces/faiblesses)
            summary = values[1]
        elif len(values) >= 3:
            strengths_raw = values[1]
            weaknesses_raw = values[2]
            if len(values) > 3:
                summary = "|".join(values[3:]).strip() or None

        # Si aucun résumé n'a été trouvé dans la ligne structurée, tenter de le
        # récupérer dans les lignes suivantes (texte libre après la data line).
        if summary is None and lines and selected_index is not None:
            remaining_lines = lines[selected_index + 1 :]
            if remaining_lines:
                summary_candidate = " ".join(remaining_lines).strip()
                if summary_candidate:
                    summary = summary_candidate

        strengths_list = [s.strip() for s in strengths_raw.split(";") if s.strip()] if strengths_raw else []
        weaknesses_list = [w.strip() for w in weaknesses_raw.split(";") if w.strip()] if weaknesses_raw else []

        return {
            "context": context,
            "synergy_score": synergy_score,
            "strengths": strengths_list or None,
            "weaknesses": weaknesses_list or None,
            "summary": summary,
            "raw_response": {"fallback_raw": raw_text},
            "build_data": build_data,
        }

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        await super().validate_inputs(inputs)

        if "build_data" in inputs:
            if not isinstance(inputs["build_data"], dict):
                raise ValueError("build_data must be a dictionary")
        elif "skill_data" in inputs:
            if not isinstance(inputs["skill_data"], dict):
                raise ValueError("skill_data must be a dictionary")
        else:
            raise ValueError("Either skill_data or build_data must be provided")

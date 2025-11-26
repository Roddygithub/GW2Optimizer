"""
Meta Analysis API Endpoints

Endpoints pour l'analyse de méta et l'importation de données GW2.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.workflows.meta_analysis_workflow import MetaAnalysisWorkflow
from app.services.gw2_api_client import GW2APIClient
from app.core.logging import logger


router = APIRouter(prefix="/meta", tags=["meta"])


# ==================== Schemas ====================


class MetaAnalysisRequest(BaseModel):
    """Requête d'analyse de méta."""

    game_mode: str = Field(..., description="Mode de jeu (zerg, raid_guild, roaming)")
    profession: Optional[str] = Field(None, description="Profession à analyser (optionnel)")
    include_api_data: bool = Field(False, description="Inclure les données de l'API GW2")
    time_range: int = Field(30, ge=1, le=365, description="Période d'analyse en jours")


class GW2DataImportRequest(BaseModel):
    """Requête d'importation de données GW2."""

    data_types: list[str] = Field(
        default=["professions", "specializations", "traits"], description="Types de données à importer"
    )
    profession: Optional[str] = Field(None, description="Profession spécifique à importer (optionnel)")


# ==================== Endpoints ====================


@router.post("/analyze")
async def analyze_meta(request: MetaAnalysisRequest):
    """
    Analyse le méta actuel pour un mode de jeu.

    Effectue une analyse complète incluant:
    - État actuel du méta
    - Détection des tendances
    - Scores de viabilité des builds
    - Recommandations d'adaptation
    - Prédictions d'évolution

    Args:
        request: Paramètres d'analyse

    Returns:
        Rapport d'analyse complet

    Raises:
        HTTPException: En cas d'erreur d'analyse
    """
    logger.info(f"Meta analysis requested for game_mode={request.game_mode}, " f"profession={request.profession}")

    try:
        # Créer et exécuter le workflow
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()

        result = await workflow.run(
            {
                "game_mode": request.game_mode,
                "profession": request.profession,
                "include_api_data": request.include_api_data,
                "time_range": request.time_range,
            }
        )

        if not result.get("success"):
            logger.error(f"Meta analysis failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail="Meta analysis failed")

        return {"success": True, "report": result.get("report"), "timestamp": result.get("execution_timestamp")}

    except ValueError as e:
        logger.error(f"Invalid input for meta analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Meta analysis failed")
        raise HTTPException(status_code=500, detail="Meta analysis failed")


@router.get("/overview/{game_mode}")
async def get_meta_overview(
    game_mode: str,
    time_range: int = Query(30, ge=1, le=365, description="Période d'analyse en jours"),
    profession: Optional[str] = Query(None, description="Profession à filtrer (optionnel)"),
):
    """Retourne une vue agrégée du méta pour un mode de jeu.

    Cette vue est pensée pour le Meta Dashboard frontend et fournit :
    - la répartition des professions (basée sur les archétypes les plus fréquents)
    - la liste des archétypes (profession + spécialisation) avec fréquence
    - les synergies communes telles que calculées par le MetaAgent
    """

    logger.info(f"Meta overview requested for game_mode={game_mode}, profession={profession}")

    try:
        from app.agents.meta_agent import MetaAgent

        agent = MetaAgent()
        await agent.initialize()

        meta_result = await agent.run(
            {
                "game_mode": game_mode,
                "profession": profession,
                "time_range": time_range,
            }
        )

        meta_snapshot = meta_result.get("meta_snapshot", {}) or {}
        common_synergies = meta_snapshot.get("common_synergies", []) or []

        # Agrégation par profession à partir des archétypes/synergies courants
        profession_counts: dict[str, int] = {}
        total_occurrences = 0

        for item in common_synergies:
            prof = item.get("profession") or "Unknown"
            occ = int(item.get("occurrences", 0) or 0)
            profession_counts[prof] = profession_counts.get(prof, 0) + occ
            total_occurrences += occ

        professions = []
        if total_occurrences > 0:
            for prof, count in sorted(profession_counts.items(), key=lambda x: x[1], reverse=True):
                professions.append(
                    {
                        "profession": prof,
                        "count": count,
                        "ratio": round(count / total_occurrences, 4),
                    }
                )

        # Les archétypes sont pour l'instant un alias structuré de common_synergies
        archetypes = [
            {
                "profession": item.get("profession"),
                "specialization": item.get("specialization"),
                "synergy_score": item.get("synergy_score"),
                "occurrences": int(item.get("occurrences", 0) or 0),
                "frequency": float(item.get("frequency", 0.0) or 0.0),
            }
            for item in common_synergies
        ]

        return {
            "success": True,
            "game_mode": game_mode,
            "professions": professions,
            "archetypes": archetypes,
            "synergies": common_synergies,
            "raw_meta": meta_result,
            "timestamp": meta_result.get("analysis_timestamp"),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Failed to get meta overview")
        raise HTTPException(status_code=500, detail="Failed to get meta overview")


@router.get("/snapshot/{game_mode}")
async def get_meta_snapshot(
    game_mode: str, profession: Optional[str] = Query(None, description="Profession à filtrer")
):
    """
    Récupère un snapshot rapide du méta actuel.

    Args:
        game_mode: Mode de jeu
        profession: Profession (optionnel)

    Returns:
        Snapshot du méta

    Raises:
        HTTPException: En cas d'erreur
    """
    logger.info(f"Meta snapshot requested for {game_mode}")

    try:
        from app.agents.meta_agent import MetaAgent

        agent = MetaAgent()
        await agent.initialize()

        result = await agent.run(
            {"game_mode": game_mode, "profession": profession, "time_range": 7}  # Snapshot sur 7 jours
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get meta snapshot")

        meta_data = result.get("result", {})

        return {
            "success": True,
            "snapshot": meta_data.get("meta_snapshot"),
            "trends": meta_data.get("trends"),
            "timestamp": meta_data.get("analysis_timestamp"),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Failed to get meta snapshot")
        raise HTTPException(status_code=500, detail="Failed to get meta snapshot")


@router.post("/import-gw2-data")
async def import_gw2_data(request: GW2DataImportRequest):
    """
    Importe les données depuis l'API officielle GW2.

    Permet d'importer:
    - Professions et leurs mécaniques
    - Spécialisations
    - Traits
    - Compétences

    Args:
        request: Types de données à importer

    Returns:
        Résumé de l'importation

    Raises:
        HTTPException: En cas d'erreur d'importation
    """
    logger.info(f"GW2 data import requested: {request.data_types}")

    try:
        client = GW2APIClient()
        imported_data = {}

        # Importer les professions
        if "professions" in request.data_types:
            if request.profession:
                profession_data = await client.get_profession(request.profession)
                imported_data["profession"] = profession_data
            else:
                professions = await client.get_all_professions_details()
                imported_data["professions"] = professions

        # Importer les spécialisations
        if "specializations" in request.data_types:
            specializations = await client.get_specializations()
            imported_data["specializations"] = specializations

        # Importer les traits
        if "traits" in request.data_types:
            traits = await client.get_traits()
            imported_data["traits"] = traits

        # Statistiques d'importation
        stats = {
            "professions_imported": len(imported_data.get("professions", [])),
            "profession_imported": "profession" in imported_data,
            "specializations_imported": len(imported_data.get("specializations", [])),
            "traits_imported": len(imported_data.get("traits", [])),
        }

        logger.info(f"GW2 data import completed: {stats}")

        return {"success": True, "stats": stats, "data": imported_data}

    except Exception:
        logger.exception("GW2 data import failed")
        raise HTTPException(status_code=500, detail="Data import failed")


@router.get("/gw2-api/professions")
async def get_gw2_professions():
    """
    Récupère la liste des professions depuis l'API GW2.

    Returns:
        Liste des professions
    """
    try:
        client = GW2APIClient()
        professions = await client.get_professions()

        return {"success": True, "professions": professions, "count": len(professions)}

    except Exception:
        logger.exception("Failed to fetch professions")
        raise HTTPException(status_code=500, detail="Failed to fetch professions")


@router.get("/gw2-api/profession/{profession_id}")
async def get_gw2_profession(profession_id: str):
    """
    Récupère les détails d'une profession depuis l'API GW2.

    Args:
        profession_id: ID de la profession (ex: "Guardian")

    Returns:
        Détails de la profession
    """
    try:
        client = GW2APIClient()
        profession = await client.get_profession(profession_id)

        return {"success": True, "profession": profession}

    except Exception:
        logger.exception("Failed to fetch profession %s", profession_id)
        raise HTTPException(status_code=500, detail="Failed to fetch profession")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Récupère les statistiques du cache API GW2.

    Returns:
        Statistiques du cache
    """
    try:
        client = GW2APIClient()
        stats = client.get_cache_stats()

        return {"success": True, "cache_stats": stats}

    except Exception:
        logger.exception("Failed to get cache stats")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")


@router.post("/cache/clear")
async def clear_cache():
    """
    Vide le cache de l'API GW2.

    Returns:
        Confirmation
    """
    try:
        client = GW2APIClient()
        client.clear_cache()

        return {"success": True, "message": "Cache cleared successfully"}

    except Exception:
        logger.exception("Failed to clear cache")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

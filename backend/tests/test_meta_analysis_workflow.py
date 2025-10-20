"""
Tests for Meta Analysis Workflow

Tests unitaires pour le workflow d'analyse de méta.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.workflows.meta_analysis_workflow import MetaAnalysisWorkflow


@pytest.mark.asyncio
class TestMetaAnalysisWorkflow:
    """Tests pour le Meta Analysis Workflow."""
    
    async def test_workflow_initialization(self):
        """Test l'initialisation du workflow."""
        workflow = MetaAnalysisWorkflow()
        
        assert workflow.name == "MetaAnalysisWorkflow"
        assert workflow.version == "1.0.0"
        assert len(workflow.steps) == 5
        
        # Vérifier les noms des étapes
        step_names = [step.name for step in workflow.steps]
        assert "collect_game_data" in step_names
        assert "analyze_meta" in step_names
        assert "detect_trends" in step_names
        assert "generate_recommendations" in step_names
        assert "create_report" in step_names
    
    async def test_workflow_run_basic(self):
        """Test l'exécution basique du workflow."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "game_mode": "zerg",
            "time_range": 30
        })
        
        assert result["success"] is True
        assert "report" in result
        assert "execution_timestamp" in result
        
        report = result["report"]
        assert report["game_mode"] == "zerg"
        assert "executive_summary" in report
        assert "meta_snapshot" in report
        assert "trends" in report
        assert "recommendations" in report
    
    async def test_workflow_with_profession(self):
        """Test le workflow avec une profession spécifique."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "game_mode": "raid_guild",
            "profession": "Guardian",
            "time_range": 14
        })
        
        assert result["success"] is True
        report = result["report"]
        
        assert report["profession"] == "Guardian"
        assert report["game_mode"] == "raid_guild"
    
    @patch('app.services.gw2_api_client.GW2APIClient.get_profession')
    async def test_workflow_with_api_data(self, mock_get_profession):
        """Test le workflow avec importation de données API."""
        # Mock de la réponse API
        mock_get_profession.return_value = {
            "id": "Guardian",
            "name": "Guardian",
            "specializations": [13, 16, 27, 42, 46, 62, 65]
        }
        
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "game_mode": "zerg",
            "profession": "Guardian",
            "include_api_data": True,
            "time_range": 30
        })
        
        assert result["success"] is True
        report = result["report"]
        
        assert report["game_data_included"] is True
        assert "game_data_summary" in report
    
    async def test_workflow_executive_summary(self):
        """Test la génération du résumé exécutif."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "game_mode": "roaming",
            "time_range": 30
        })
        
        assert result["success"] is True
        report = result["report"]
        
        summary = report["executive_summary"]
        assert "total_trends_detected" in summary
        assert "average_build_viability" in summary
        assert "total_recommendations" in summary
        assert "meta_stability" in summary
        assert "key_insights" in summary
        
        # Vérifier que la stabilité est valide
        assert summary["meta_stability"] in ["stable", "shifting", "volatile"]
    
    async def test_workflow_with_builds(self):
        """Test le workflow avec des builds à analyser."""
        test_builds = [
            {
                "id": "build_1",
                "role": "support",
                "profession": "Guardian"
            },
            {
                "id": "build_2",
                "role": "dps",
                "profession": "Warrior"
            }
        ]
        
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "game_mode": "zerg",
            "current_builds": test_builds,
            "time_range": 30
        })
        
        assert result["success"] is True
        report = result["report"]
        
        # Vérifier que les scores de viabilité sont présents
        assert "viability_scores" in report
        viability_scores = report["viability_scores"]
        
        if viability_scores:
            for score in viability_scores.values():
                assert 0.0 <= score <= 1.0
    
    async def test_workflow_invalid_game_mode(self):
        """Test la validation du mode de jeu."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "game_mode": "invalid_mode",
            "time_range": 30
        })
        
        assert result["success"] is False
        assert "error" in result
    
    async def test_workflow_missing_game_mode(self):
        """Test l'erreur si game_mode est manquant."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        result = await workflow.run({
            "time_range": 30
        })
        
        assert result["success"] is False
        assert "error" in result
    
    async def test_workflow_meta_stability_assessment(self):
        """Test l'évaluation de la stabilité du méta."""
        workflow = MetaAnalysisWorkflow()
        
        # Test stable
        trends_stable = []
        stability = workflow._assess_meta_stability(trends_stable)
        assert stability == "stable"
        
        # Test shifting
        trends_shifting = [
            {"change_percentage": 0.25, "confidence": 0.8}
        ]
        stability = workflow._assess_meta_stability(trends_shifting)
        assert stability == "shifting"
        
        # Test volatile
        trends_volatile = [
            {"change_percentage": 0.25, "confidence": 0.8},
            {"change_percentage": 0.30, "confidence": 0.9},
            {"change_percentage": 0.22, "confidence": 0.75}
        ]
        stability = workflow._assess_meta_stability(trends_volatile)
        assert stability == "volatile"
    
    async def test_workflow_key_insights_extraction(self):
        """Test l'extraction des insights clés."""
        workflow = MetaAnalysisWorkflow()
        
        trends = [
            {
                "description": "Augmentation des builds support",
                "confidence": 0.85
            }
        ]
        
        recommendations = [
            {"priority": "high", "description": "Action 1"},
            {"priority": "medium", "description": "Action 2"}
        ]
        
        viability_scores = {
            "build_1": 0.3,
            "build_2": 0.8,
            "build_3": 0.4
        }
        
        insights = workflow._extract_key_insights(
            trends,
            recommendations,
            viability_scores
        )
        
        assert isinstance(insights, list)
        assert len(insights) > 0
    
    async def test_workflow_cleanup(self):
        """Test le nettoyage du workflow."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        assert workflow._is_initialized is True
        
        await workflow.cleanup()
        
        assert workflow._is_initialized is False
    
    async def test_workflow_step_status_updates(self):
        """Test la mise à jour des statuts des étapes."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        # Exécuter le workflow
        result = await workflow.run({
            "game_mode": "zerg",
            "time_range": 30
        })
        
        assert result["success"] is True
        
        # Vérifier que les étapes existent
        assert len(workflow.steps) == 5
        assert all(hasattr(step, 'name') for step in workflow.steps)
    
    async def test_workflow_game_data_summary(self):
        """Test le résumé des données de jeu."""
        workflow = MetaAnalysisWorkflow()
        
        game_data = {
            "success": True,
            "profession": {"id": "Guardian", "name": "Guardian"},
            "specializations": [
                {"id": 27, "name": "Dragonhunter"},
                {"id": 62, "name": "Firebrand"}
            ]
        }
        
        summary = workflow._summarize_game_data(game_data)
        
        assert summary["data_collected"] is True
        assert summary["profession_data"] is True
        assert summary["specializations_count"] == 2
    
    async def test_workflow_different_time_ranges(self):
        """Test le workflow avec différentes périodes d'analyse."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        # Test avec 7 jours
        result_7d = await workflow.run({
            "game_mode": "zerg",
            "time_range": 7
        })
        assert result_7d["success"] is True
        assert result_7d["report"]["analysis_period"] == "7 days"
        
        # Test avec 90 jours
        result_90d = await workflow.run({
            "game_mode": "zerg",
            "time_range": 90
        })
        assert result_90d["success"] is True
        assert result_90d["report"]["analysis_period"] == "90 days"
    
    async def test_workflow_all_game_modes(self):
        """Test le workflow avec tous les modes de jeu."""
        workflow = MetaAnalysisWorkflow()
        await workflow.initialize()
        
        game_modes = ["zerg", "raid_guild", "roaming"]
        
        for mode in game_modes:
            result = await workflow.run({
                "game_mode": mode,
                "time_range": 30
            })
            
            assert result["success"] is True
            assert result["report"]["game_mode"] == mode

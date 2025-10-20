"""Tests for AI Workflows."""

import pytest
from app.workflows.build_optimization_workflow import BuildOptimizationWorkflow
from app.workflows.team_analysis_workflow import TeamAnalysisWorkflow
from app.workflows.learning_workflow import LearningWorkflow

pytestmark = pytest.mark.asyncio


class TestBuildOptimizationWorkflow:
    """Tests for BuildOptimizationWorkflow."""

    async def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = BuildOptimizationWorkflow()
        assert workflow.name == "BuildOptimizationWorkflow"
        assert len(workflow.steps) > 0
        assert workflow.status.value == "pending"

    async def test_workflow_input_validation_success(self):
        """Test workflow input validation with valid data."""
        workflow = BuildOptimizationWorkflow()
        inputs = {"profession": "Guardian", "role": "Support", "game_mode": "WvW"}
        await workflow.validate_inputs(inputs)

    async def test_workflow_input_validation_missing_profession(self):
        """Test workflow input validation fails with missing profession."""
        workflow = BuildOptimizationWorkflow()
        inputs = {"role": "Support", "game_mode": "WvW"}

        with pytest.raises(ValueError, match="Missing required field"):
            await workflow.validate_inputs(inputs)

    async def test_workflow_input_validation_with_team(self):
        """Test workflow input validation with team composition."""
        workflow = BuildOptimizationWorkflow()
        inputs = {
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW",
            "team_composition": ["Guardian", "Warrior", "Mesmer"],
        }
        await workflow.validate_inputs(inputs)

    async def test_workflow_steps_defined(self):
        """Test workflow has defined steps."""
        workflow = BuildOptimizationWorkflow()
        assert len(workflow.steps) >= 2
        assert any("recommendation" in step.name.lower() for step in workflow.steps)


class TestTeamAnalysisWorkflow:
    """Tests for TeamAnalysisWorkflow."""

    async def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = TeamAnalysisWorkflow()
        assert workflow.name == "TeamAnalysisWorkflow"
        assert len(workflow.steps) > 0
        assert workflow.status.value == "pending"

    async def test_workflow_input_validation_success(self):
        """Test workflow input validation with valid data."""
        workflow = TeamAnalysisWorkflow()
        inputs = {"professions": ["Guardian", "Warrior", "Mesmer"], "game_mode": "WvW"}
        await workflow.validate_inputs(inputs)

    async def test_workflow_input_validation_missing_professions(self):
        """Test workflow input validation fails with missing professions."""
        workflow = TeamAnalysisWorkflow()
        inputs = {"game_mode": "WvW"}

        with pytest.raises(ValueError, match="Missing required field"):
            await workflow.validate_inputs(inputs)

    async def test_workflow_input_validation_with_optimization(self):
        """Test workflow input validation with optimization enabled."""
        workflow = TeamAnalysisWorkflow()
        inputs = {
            "professions": ["Guardian", "Warrior", "Mesmer"],
            "game_mode": "WvW",
            "optimize": True,
            "max_changes": 2,
        }
        await workflow.validate_inputs(inputs)

    async def test_workflow_steps_defined(self):
        """Test workflow has defined steps."""
        workflow = TeamAnalysisWorkflow()
        assert len(workflow.steps) >= 1
        assert any("analysis" in step.name.lower() or "synergy" in step.name.lower() for step in workflow.steps)


class TestLearningWorkflow:
    """Tests for LearningWorkflow."""

    async def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = LearningWorkflow()
        assert workflow.name == "LearningWorkflow"
        assert workflow.status.value == "pending"

    async def test_workflow_is_placeholder(self):
        """Test workflow is marked as placeholder."""
        workflow = LearningWorkflow()
        # LearningWorkflow is a placeholder for future integration
        assert hasattr(workflow, "name")
        assert hasattr(workflow, "status")

"""
Base classes for AI Agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """
    Abstract Base Class for all AI agents.

    Each agent must implement the `run` method, which takes a dictionary
    of inputs and returns a dictionary with the results.
    """

    @abstractmethod
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task."""
        pass

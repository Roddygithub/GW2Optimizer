"""Chat service for conversational AI."""

import re
from typing import List

from app.core.logging import logger
from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.ai.ollama_service import OllamaService


class ChatService:
    """Service for handling chat interactions."""

    def __init__(self) -> None:
        """Initialize chat service."""
        self.ollama = OllamaService()
        self.system_prompt = """You are an expert Guild Wars 2 WvW (World vs World) strategist and build optimizer.

Your expertise includes:
- All 9 professions and their elite specializations
- WvW meta builds for roaming, raid guild, and zerg play
- Boon coverage, combo fields, and team synergies
- Current meta compositions and counters
- GW2Skill build links parsing and analysis

When users ask about builds or teams:
1. Consider the game mode (roaming/raid guild/zerg)
2. Analyze role requirements and synergies
3. Suggest meta-appropriate builds
4. Explain your reasoning clearly

If a user provides a GW2Skill URL, acknowledge it and offer to analyze it.
Be concise, practical, and always meta-aware."""

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and generate response.

        Args:
            request: Chat request with message and history

        Returns:
            Chat response with suggestions
        """
        try:
            # Build conversation history
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add conversation history
            for msg in request.conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

            # Add context if provided
            if request.context:
                messages.append({"role": "system", "content": f"Current context:\n{request.context}"})

            # Add user message
            messages.append({"role": "user", "content": request.message})

            # Detect GW2Skill URLs
            gw2skill_urls = self._extract_gw2skill_urls(request.message)

            # Determine action required
            action_required = None
            if gw2skill_urls:
                action_required = "parse_build"
            elif any(
                keyword in request.message.lower() for keyword in ["optimize", "team", "composition", "squad", "group"]
            ):
                action_required = "optimize_team"

            # Generate response
            response_text = await self.ollama.chat(messages, temperature=0.7)

            # Extract suggestions
            suggestions = self._extract_suggestions(response_text)

            return ChatResponse(
                response=response_text,
                suggestions=suggestions,
                builds_mentioned=gw2skill_urls,
                action_required=action_required,
            )

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise

    def _extract_gw2skill_urls(self, text: str) -> List[str]:
        """Extract GW2Skill URLs from text."""
        # Match various GW2Skill URL formats
        patterns = [
            r"http[s]?://(?:www\.)?gw2skills\.net/editor/[^\s]+",
            r"http[s]?://(?:en\.)?gw2skills\.net/editor/[^\s]+",
            r"gw2skills\.net/editor/[^\s]+",
        ]

        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))

        return list(set(urls))  # Remove duplicates

    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract actionable suggestions from response."""
        suggestions = []

        # Look for bullet points or numbered lists
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("- ", "• ", "* ", "1.", "2.", "3.")):
                suggestion = re.sub(r"^[-•*\d.]\s*", "", line).strip()
                if len(suggestion) > 10:  # Meaningful suggestions only
                    suggestions.append(suggestion)

        return suggestions[:5]  # Limit to 5 suggestions

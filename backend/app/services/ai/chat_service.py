"""Chat service for handling AI-powered conversations with circuit breaker and retry logic."""

import re
import json
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlunparse

from app.core.logging import logger
from app.core.circuit_breaker import circuit_breaker, CircuitBreakerError, chat_service_circuit_breaker, CircuitBreaker
from app.models.chat import ChatRequest, ChatResponse, BuildSuggestion
from app.services.ai.ollama_service import OllamaService

# Constants
MAX_MESSAGE_LENGTH = 2000
MAX_SUGGESTIONS = 5
DEFAULT_TEMPERATURE = 0.7


class ChatService:
    """
    Service for handling AI-powered chat interactions with circuit breaker protection.

    This service processes chat messages, manages conversation history, and interacts
    with the Ollama AI service to generate responses. It includes circuit breaker
    protection to handle service failures gracefully.
    """

    def __init__(self, client: Optional[OllamaService] = None, breaker: Optional[CircuitBreaker] = None) -> None:
        """
        Initialize the chat service with default configuration.

        Sets up the Ollama service and defines the system prompt that guides
        the AI's behavior and expertise.
        """
        self.ollama = client or OllamaService()
        selected_breaker = breaker or chat_service_circuit_breaker
        # Maintain backward compatibility with tests expecting either attribute name
        self.breaker = selected_breaker
        self.circuit_breaker = selected_breaker
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
        Process a chat message and generate a response with circuit breaker protection.

        Args:
            request: Chat request containing message, history, and context

        Returns:
            ChatResponse with AI-generated response and metadata

        Raises:
            HTTPException: If there's an error processing the message
            CircuitBreakerError: If the circuit is open
        """
        try:
            # Validate input
            if not request.message or len(request.message) > MAX_MESSAGE_LENGTH:
                raise ValueError(f"Message must be between 1 and {MAX_MESSAGE_LENGTH} characters")

            # Build conversation history with system prompt
            messages = self._build_messages(request)

            # Extract build information if GW2Skill URLs are present
            build_suggestions = []
            gw2skill_urls = self._extract_gw2skill_urls(request.message)

            # Determine if this is a build or team optimization request
            action_required = self._determine_action_required(request.message, gw2skill_urls)

            try:
                response_text = await self._call_model(messages)

                # Extract suggestions and build info
                suggestions = self._extract_suggestions(response_text)

                # If we have GW2Skill URLs, create build suggestions
                if gw2skill_urls:
                    build_suggestions = [BuildSuggestion(gw2skills_url=url) for url in gw2skill_urls]

                return ChatResponse(
                    response=response_text,
                    suggestions=suggestions[:MAX_SUGGESTIONS],
                    builds=build_suggestions,
                    action_required=action_required,
                    metadata={"model_used": "ollama/llama3", "tokens_generated": len(response_text.split())},
                )

            except asyncio.TimeoutError:
                logger.error("AI service timeout")
                return ChatResponse(
                    response="I'm currently experiencing high demand. Please try again in a moment.",
                    suggestions=["Try again", "Ask a different question"],
                    action_required=action_required,
                    metadata={"error": "timeout"},
                )

        except CircuitBreakerError as e:
            logger.warning(f"Circuit breaker open: {e}")
            return ChatResponse(
                response="I'm currently unavailable. Please try again in a few moments.",
                suggestions=["Try again later", "Check back soon"],
                metadata={"error": "service_unavailable", "circuit_state": e.circuit_breaker.state},
            )

        except Exception as e:
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            return ChatResponse(
                response="I encountered an error processing your request. Please try again.",
                suggestions=["Try again", "Rephrase your question"],
                metadata={"error": str(e)[:100]},
            )

    @circuit_breaker()
    async def _call_model(self, messages: List[Dict[str, str]]) -> str:
        """Execute the model call with circuit breaker protection."""
        return await asyncio.wait_for(self.ollama.chat(messages=messages, temperature=DEFAULT_TEMPERATURE), timeout=30)

    def _build_messages(self, request: ChatRequest) -> List[Dict[str, str]]:
        """
        Build the conversation history with system prompt and context.

        Args:
            request: The chat request containing message and history

        Returns:
            List of message dictionaries for the AI model
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history if available
        if request.conversation_history:
            for msg in request.conversation_history:
                role = msg.get("role", "user")
                if role not in ["user", "assistant", "system"]:
                    role = "user"  # Default to user role if invalid
                messages.append({"role": role, "content": msg.get("content", "")})

        # Add context if provided
        if request.context:
            context_str = (
                json.dumps(request.context, indent=2) if isinstance(request.context, dict) else str(request.context)
            )
            messages.append({"role": "system", "content": f"Current context:\n{context_str}"})

        # Add user message
        messages.append({"role": "user", "content": request.message})

        return messages

    def _determine_action_required(self, message: str, gw2skill_urls: List[str]) -> Optional[str]:
        """
        Determine what action is required based on the message content.

        Args:
            message: The user's message
            gw2skill_urls: List of GW2Skill URLs found in the message

        Returns:
            String indicating the required action, or None
        """
        if gw2skill_urls:
            return "parse_build"

        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ["optimize", "team", "composition", "squad", "group"]):
            return "optimize_team"

        if any(keyword in message_lower for keyword in ["build", "gear", "traits", "skills"]):
            return "suggest_build"

        return None

    def _extract_gw2skill_urls(self, text: str) -> List[str]:
        """
        Extract GW2Skill URLs from the given text.

        Args:
            text: The text to search for GW2Skill URLs

        Returns:
            List of unique GW2Skill URLs found in the text
        """
        if not text:
            return []

        patterns = [
            r"(?<![A-Za-z0-9.-])(https?://(?:www\.)?gw2skills\.net/editor/[^\s]+)",
            r"(?<![A-Za-z0-9.-])(https?://(?:en\.)?gw2skills\.net/editor/[^\s]+)",
            r"(?<![A-Za-z0-9.-])(//gw2skills\.net/editor/[^\s]+)",
            r"(?<![A-Za-z0-9.-])(gw2skills\.net/editor/[^\s]+)",
        ]

        candidates = []
        for pattern in patterns:
            candidates.extend(match.group(1) for match in re.finditer(pattern, text, re.IGNORECASE))

        sanitized_urls: List[str] = []
        seen = set()
        for candidate in candidates:
            sanitized = self._sanitize_gw2skill_url(candidate)
            if sanitized and sanitized not in seen:
                seen.add(sanitized)
                sanitized_urls.append(sanitized)

        return sanitized_urls

    def _sanitize_gw2skill_url(self, url: str) -> Optional[str]:
        """Return a normalized GW2Skill URL if the host is trusted, else None."""

        if not url:
            return None

        clean_url = re.sub(r"[^\w\-~.:/#?&;=%]+$", "", url.strip())
        if not clean_url:
            return None

        lowered = clean_url.lower()
        if lowered.startswith("//"):
            candidate = f"https:{clean_url}"
        elif lowered.startswith("http://") or lowered.startswith("https://"):
            candidate = clean_url
        else:
            candidate = f"https://{clean_url}"

        parsed = urlparse(candidate)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return None

        if hostname != "gw2skills.net" and not hostname.endswith(".gw2skills.net"):
            return None

        if not (parsed.path or "").lower().startswith("/editor/"):
            return None

        scheme = "https"
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            host, _, port = netloc.partition(":")
            netloc = f"{host.lower()}:{port}"

        normalized = urlunparse((scheme, netloc, parsed.path, "", parsed.query, parsed.fragment))
        return normalized

    def _extract_suggestions(self, text: str, max_length: int = 100) -> List[str]:
        """
        Extract actionable suggestions from the AI's response text.

        Args:
            text: The AI's response text
            max_length: Maximum length for each suggestion

        Returns:
            List of extracted suggestions
        """
        if not text:
            return []

        suggestions = []

        # Look for bullet points or numbered lists
        lines = text.split("\n")
        for line in lines:
            line = line.strip()

            # Check for various bullet point formats
            if re.match(r"^[•*-]\s+.+", line) or re.match(r"^\d+\.\s+.+", line):
                # Remove bullet/number and clean up
                suggestion = re.sub(r"^[•*\-]\s*|^\d+\.\s*", "", line).strip()

                # Only include meaningful suggestions
                if 10 < len(suggestion) <= max_length and not suggestion.endswith((":", "?")):
                    # Capitalize first letter if needed
                    if suggestion and not suggestion[0].isupper():
                        suggestion = suggestion[0].upper() + suggestion[1:]
                    suggestions.append(suggestion)

        # If no bullet points found, look for question marks or other patterns
        if not suggestions and "?" in text:
            # Split on sentences ending with question marks
            sentences = re.split(r"(?<=[.!?])\s+", text)
            suggestions = [s.strip() for s in sentences if "?" in s and 10 < len(s) <= max_length]

        # Ensure we don't return too many or too long suggestions
        return [s[:max_length].strip() for s in suggestions[:MAX_SUGGESTIONS] if s.strip()]

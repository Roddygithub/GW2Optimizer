"""Ollama service for AI interactions."""

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


class OllamaService:
    """Service for interacting with Ollama AI."""

    def __init__(self) -> None:
        """Initialize Ollama service."""
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = 300.0  # Augmenté à 5 minutes

    async def check_health(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Creativity (0-1)
            max_tokens: Max response length

        Returns:
            Generated text
        """
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            schema: Expected JSON schema

        Returns:
            Parsed JSON response
        """
        full_system = system_prompt or ""
        if schema:
            full_system += f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        else:
            full_system += "\n\nRespond with valid JSON only, no additional text."

        response = await self.generate(
            prompt=prompt,
            system_prompt=full_system,
            temperature=0.3,  # Lower temperature for structured output
        )

        try:
            # Try to extract JSON from response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {response}")
            raise ValueError(f"Failed to parse JSON response: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """
        Continue a conversation.

        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            temperature: Creativity (0-1)

        Returns:
            Assistant response
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            logger.info(f"Sending request to Ollama with model: {self.model}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

            start_time = time.time()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(
                        f"{self.host}/api/chat",
                        json=payload,
                    )
                    response.raise_for_status()

                    elapsed = time.time() - start_time
                    logger.info(f"Ollama response received in {elapsed:.2f} seconds")

                    data = response.json()
                    logger.debug(f"Ollama response: {json.dumps(data, indent=2)}")

                    content = data.get("message", {}).get("content", "")
                    logger.info(f"Extracted content length: {len(content)} characters")

                    return content
                except httpx.HTTPStatusError as e:
                    logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
                    raise
                except httpx.RequestError as e:
                    logger.error(f"Request to Ollama failed: {str(e)}")
                    raise

        except Exception as e:
            logger.error(f"Error in chat with Ollama: {e}")
            raise

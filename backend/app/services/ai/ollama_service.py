"""Ollama service for AI interactions."""

import json
import re
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
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        chat_payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # Essayer d'abord l'endpoint /api/chat (Ollama récents)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.host}/api/chat", json=chat_payload)
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                if content:
                    return content
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning("Ollama /api/chat returned 404, falling back to /api/generate")
            else:
                logger.error(f"Ollama /api/chat error: {e}")
                raise
        except Exception as e:
            logger.error(f"Error generating with Ollama via /api/chat: {e}")
            raise

        # Fallback: utiliser /api/generate (anciennes versions d'Ollama)
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            generate_payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.host}/api/generate", json=generate_payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except Exception as e:
            logger.error(f"Error generating with Ollama via /api/generate: {e}")
            raise

    def _clean_json_string(self, text: str) -> str:
        """Extract the first JSON object from a text blob, if possible.

        This is useful when the model wraps JSON in markdown (```json ... ```)
        or adds explanatory text around the JSON. If no object is found,
        returns the original text.
        """

        # Remove common markdown fences first to simplify the text
        cleaned = text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]

        # Try to extract the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return match.group(0)
        return cleaned

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 512,
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

        raw_response = await self.generate(
            prompt=prompt,
            system_prompt=full_system,
            temperature=0.3,  # Lower temperature for structured output
            max_tokens=max_tokens,
        )

        # First attempt: direct JSON parse
        candidate = raw_response.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Second attempt: extract the first JSON object from the text
            cleaned = self._clean_json_string(candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON response after cleaning: {e}\n"
                    f"Raw response: {raw_response}\nCleaned candidate: {cleaned}"
                )
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

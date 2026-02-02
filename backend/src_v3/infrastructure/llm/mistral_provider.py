"""
Mistral LLM provider implementation

Provides integration with Mistral AI API

Supports:
- mistral-small (fast, cost-effective)
- mistral-medium (balanced)
- mistral-large (advanced reasoning)

Configuration:
    api_key: Mistral API key
    model: Model name (default: mistral-small)
    temperature: Sampling temperature (default: 0.7)
    timeout: Request timeout in seconds (default: 60)

FIX Cortez67:
- Added persistent HTTP client with connection pooling (CRITICAL-005)
- Added retry jitter to prevent thundering herd (HIGH-001)
"""
from typing import Optional, Dict, Any, List, AsyncIterator
import logging
import httpx
import json
import asyncio
import random

from .base import LLMProvider, LLMMessage, LLMResponse, LLMRole

logger = logging.getLogger(__name__)


class MistralProvider(LLMProvider):
    """
    Mistral AI LLM provider

    Supports models:
    - mistral-small: Fast, efficient
    - mistral-medium: Balanced performance
    - mistral-large: Advanced reasoning

    Configuration:
        api_key: Mistral API key (required)
        model: Default model name (default: mistral-small)
        temperature: Sampling temperature (default: 0.7)
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum retry attempts (default: 3)
    """

    # Model definitions
    SMALL_MODEL = "mistral-small-latest"
    MEDIUM_MODEL = "mistral-medium-latest"
    LARGE_MODEL = "mistral-large-latest"
    
    # Base URL for Mistral API
    BASE_URL = "https://api.mistral.ai/v1"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # Configuration with sensible defaults
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("Mistral API key is required. Set MISTRAL_API_KEY environment variable.")

        self.model = self.config.get("model", self.SMALL_MODEL)
        self.temperature = self.config.get("temperature", 0.7)
        self.timeout = self.config.get("timeout", 60.0)

        # Retry configuration
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1.0)
        self.retry_backoff = self.config.get("retry_backoff", 2.0)

        # FIX Cortez67 (CRITICAL-005): Persistent HTTP client with connection pooling
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()

        # FIX Cortez67: Connection pool configuration
        self._max_keepalive_connections = self.config.get("max_keepalive_connections", 20)
        self._max_connections = self.config.get("max_connections", 100)
        self._keepalive_expiry = self.config.get("keepalive_expiry", 30.0)

        # FIX Cortez69 CRIT-LLM-002: Concurrency control to prevent connection exhaustion
        self._max_concurrent = self.config.get("max_concurrent", 10)
        self._semaphore: Optional[asyncio.Semaphore] = None
        # FIX Cortez70 CRIT-LLM-002: Lock for thread-safe semaphore initialization
        self._semaphore_lock = asyncio.Lock()

        logger.info(
            "MistralProvider initialized",
            extra={
                "model": self.model,
                "temperature": self.temperature,
                "timeout": self.timeout,
                "max_connections": self._max_connections
            }
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """
        FIX Cortez67 (CRITICAL-005): Get or create persistent HTTP client.

        Uses double-checked locking for thread safety and connection pooling
        for performance. This prevents creating new TCP connections for each request.
        """
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    self._client = httpx.AsyncClient(
                        timeout=self.timeout,
                        limits=httpx.Limits(
                            max_keepalive_connections=self._max_keepalive_connections,
                            max_connections=self._max_connections,
                            keepalive_expiry=self._keepalive_expiry
                        ),
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}"
                        }
                    )
                    logger.debug("Created persistent HTTP client for Mistral")
        return self._client

    async def _get_semaphore(self) -> asyncio.Semaphore:
        """
        FIX Cortez69 CRIT-LLM-002: Lazy initialization of semaphore.
        FIX Cortez70 CRIT-LLM-002: Use double-checked locking for thread safety.
        """
        if self._semaphore is None:
            async with self._semaphore_lock:
                if self._semaphore is None:
                    self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        FIX Cortez67 (HIGH-001): Calculate retry delay with jitter.

        Adds random jitter to prevent thundering herd problem when
        multiple clients retry simultaneously after a service recovery.
        """
        base_delay = self.retry_delay * (self.retry_backoff ** attempt)
        # Add jitter: random value between 0 and 50% of base delay
        jitter = random.uniform(0, base_delay * 0.5)
        return base_delay + jitter

    async def close(self) -> None:
        """
        FIX Cortez67: Close the HTTP client and release connections.

        Should be called during application shutdown.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Mistral HTTP client closed")

    def _convert_messages_to_mistral_format(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """
        Convert LLMMessage list to Mistral API format
        
        Mistral expects:
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
        """
        mistral_messages = []
        
        for msg in messages:
            role_mapping = {
                LLMRole.SYSTEM: "system",
                LLMRole.USER: "user",
                LLMRole.ASSISTANT: "assistant"
            }
            
            mistral_messages.append({
                "role": role_mapping.get(msg.role, "user"),
                "content": msg.content
            })
        
        return mistral_messages

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion from messages using Mistral API
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response (optional)
            **kwargs: Additional parameters
        
        Returns:
            LLMResponse with generated content and metadata
        """
        # Determine which model to use
        model = kwargs.get("model") or self.model
        
        # Auto-select model based on task type
        if kwargs.get("is_code_analysis", False) and model == self.SMALL_MODEL:
            model = self.LARGE_MODEL
            logger.info("Switching to Large model for code analysis")
        
        # Convert messages to Mistral format
        mistral_messages = self._convert_messages_to_mistral_format(messages)
        
        # Build request payload
        payload = {
            "model": model,
            "messages": mistral_messages,
            "temperature": temperature,
            "top_p": 0.95
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # FIX Cortez67 (CRITICAL-005): Use persistent client instead of creating new one
        client = await self._get_client()
        url = f"{self.BASE_URL}/chat/completions"

        # FIX Cortez69 CRIT-LLM-002: Use semaphore to limit concurrent requests
        # FIX Cortez70 CRIT-LLM-002: Use await for async _get_semaphore
        semaphore = await self._get_semaphore()
        async with semaphore:
            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    logger.debug(
                        "Sending request to Mistral (attempt %d/%d)",
                        attempt + 1, self.max_retries,
                        extra={
                            "model": model,
                            "messages_count": len(messages),
                            "temperature": temperature
                        }
                    )

                    response = await client.post(url, json=payload)

                    response.raise_for_status()
                    result = response.json()

                    # Extract content from response
                    if "choices" not in result or not result["choices"]:
                        raise ValueError("No choices in Mistral response")

                    choice = result["choices"][0]
                    content = choice["message"]["content"]

                    # Extract usage metadata
                    usage_data = result.get("usage", {})
                    usage = {
                        "prompt_tokens": usage_data.get("prompt_tokens", 0),
                        "completion_tokens": usage_data.get("completion_tokens", 0),
                        "total_tokens": usage_data.get("total_tokens", 0)
                    }

                    logger.info(
                        "Mistral request successful",
                        extra={
                            "model": model,
                            "usage": usage,
                            "finish_reason": choice.get("finish_reason", "stop")
                        }
                    )

                    return LLMResponse(
                        content=content,
                        model=model,
                        usage=usage,
                        metadata={
                            "finish_reason": choice.get("finish_reason", "stop")
                        }
                    )

                except httpx.HTTPStatusError as e:
                    logger.warning(
                        "Mistral HTTP error (attempt %d/%d): %s",
                        attempt + 1, self.max_retries, e.response.status_code,
                        extra={"response": e.response.text}
                    )

                    # Don't retry on client errors (4xx)
                    if 400 <= e.response.status_code < 500:
                        raise

                    # Retry on server errors (5xx)
                    if attempt < self.max_retries - 1:
                        # FIX Cortez67 (HIGH-001): Use jitter delay
                        delay = self._calculate_retry_delay(attempt)
                        logger.debug("Retrying in %.2f seconds (with jitter)", delay)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise

                except Exception as e:
                    logger.error(
                        "Mistral request failed (attempt %d/%d): %s",
                        attempt + 1, self.max_retries, e,
                        exc_info=True
                    )

                    if attempt < self.max_retries - 1:
                        # FIX Cortez67 (HIGH-001): Use jitter delay
                        delay = self._calculate_retry_delay(attempt)
                        logger.debug("Retrying in %.2f seconds (with jitter)", delay)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion from messages
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
        
        Yields:
            Chunks of generated content
        """
        model = kwargs.get("model") or self.model
        
        if kwargs.get("is_code_analysis", False) and model == self.SMALL_MODEL:
            model = self.LARGE_MODEL
        
        # Convert messages to Mistral format
        mistral_messages = self._convert_messages_to_mistral_format(messages)
        
        # Build request payload
        payload = {
            "model": model,
            "messages": mistral_messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # FIX Cortez67 (CRITICAL-005): Use persistent client
        client = await self._get_client()
        url = f"{self.BASE_URL}/chat/completions"

        # FIX Cortez70 CRIT-LLM-003: Apply semaphore to streaming to prevent connection exhaustion
        semaphore = await self._get_semaphore()
        async with semaphore:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip() or line.strip() == "data: [DONE]":
                        continue

                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])

                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            # FIX Cortez53: Use lazy logging
                            logger.debug("Skipping non-JSON line: %s", line)
                            continue

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximate)
        
        Uses word count * 1.3 as rough estimate
        
        Args:
            text: Input text
            
        Returns:
            Approximate token count
        """
        words = len(text.split())
        return int(words * 1.3)

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming"""
        return True

    async def analyze_complexity(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze if prompt needs advanced model
        
        Args:
            prompt: The user prompt
            
        Returns:
            Dict with needs_large, reason, confidence
        """
        # Simple heuristic for Mistral
        prompt_lower = prompt.lower()
        
        complex_keywords = [
            "algorithm", "complexity", "optimize", "debug",
            "architecture", "design pattern", "refactor"
        ]
        
        needs_large = any(keyword in prompt_lower for keyword in complex_keywords)
        
        return {
            "needs_pro": needs_large,  # Keep same interface as Gemini
            "reason": "Complex analysis detected" if needs_large else "Simple query",
            "confidence": 0.8 if needs_large else 0.7
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "provider": "mistral",
            "model": self.model,
            "small_model": self.SMALL_MODEL,
            "large_model": self.LARGE_MODEL,
            "supports_streaming": True,
            "supports_code_analysis": True,
            "supports_smart_routing": True,
            "context_window": 32000
        }

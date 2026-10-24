"""
core/gateway/providers/groq_adapter.py
Groq Cloud API adapter providing ultra-low-latency LPU inference.
Strictly separated from xAI Grok.
"""

import os
import time
import httpx
import logging
from typing import Dict, Any, List, Optional

from core.interfaces.model_gateway import InferenceRequest, InferenceResponse, ModelCapability
from core.gateway.providers.base import BaseProviderAdapter, ProviderHealth, mask_secret

logger = logging.getLogger("GroqAdapter")


class GroqAdapter(BaseProviderAdapter):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_id="groq", is_local=False)
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1"
        self.default_model = "llama-3.3-70b-versatile"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_masked_key(self) -> str:
        return mask_secret(self.api_key)

    def get_capabilities(self) -> List[ModelCapability]:
        return [
            ModelCapability(
                provider_id="groq",
                model_id="llama-3.3-70b-versatile",
                context_window=128000,
                supports_tools=True,
                supports_streaming=True,
                is_local=False,
                cost_per_1k_tokens=0.0
            ),
            ModelCapability(
                provider_id="groq",
                model_id="llama-3.1-8b-instant",
                context_window=128000,
                supports_tools=True,
                supports_streaming=True,
                is_local=False,
                cost_per_1k_tokens=0.0
            )
        ]

    async def check_health(self) -> ProviderHealth:
        if not self.is_available():
            return ProviderHealth(
                provider_id="groq",
                is_healthy=False,
                status_message="API key not configured."
            )

        start = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/models", headers=headers)
                latency_ms = (time.time() - start) * 1000.0
                if r.status_code == 200:
                    return ProviderHealth(
                        provider_id="groq",
                        is_healthy=True,
                        status_message="Online (Authenticated)",
                        latency_ms=round(latency_ms, 2)
                    )
                return ProviderHealth(
                    provider_id="groq",
                    is_healthy=False,
                    status_message=f"HTTP {r.status_code} ({r.text[:60]})",
                    latency_ms=round(latency_ms, 2)
                )
        except Exception as e:
            return ProviderHealth(
                provider_id="groq",
                is_healthy=False,
                status_message=f"Network error ({type(e).__name__})"
            )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_available():
            raise PermissionError("Groq API key is not configured.")

        start = time.time()
        model_to_use = request.preferred_model or self.default_model

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": min(request.max_tokens, 8192)
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                r = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                duration = time.time() - start
                self.record_metrics(duration, success=True)

                usage = data.get("usage", {})
                return InferenceResponse(
                    content=content,
                    model_used=model_to_use,
                    provider_used="groq",
                    is_local=False,
                    latency_seconds=duration,
                    token_usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    }
                )
        except Exception as e:
            duration = time.time() - start
            self.record_metrics(duration, success=False)
            logger.error(f"Groq generation failed: {e}")
            raise

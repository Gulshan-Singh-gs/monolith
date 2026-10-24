"""
core/gateway/providers/gemini_adapter.py
Google Gemini Cloud API adapter providing multi-modal long-context inference.
"""

import os
import time
import httpx
import logging
from typing import Dict, Any, List, Optional

from core.interfaces.model_gateway import InferenceRequest, InferenceResponse, ModelCapability
from core.gateway.providers.base import BaseProviderAdapter, ProviderHealth, mask_secret

logger = logging.getLogger("GeminiAdapter")


class GeminiAdapter(BaseProviderAdapter):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_id="gemini", is_local=False)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.default_model = "gemini-1.5-flash"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_masked_key(self) -> str:
        return mask_secret(self.api_key)

    def get_capabilities(self) -> List[ModelCapability]:
        return [
            ModelCapability(
                provider_id="gemini",
                model_id="gemini-1.5-flash",
                context_window=1000000,
                supports_tools=True,
                supports_streaming=True,
                is_local=False,
                cost_per_1k_tokens=0.0
            ),
            ModelCapability(
                provider_id="gemini",
                model_id="gemini-1.5-pro",
                context_window=2000000,
                supports_tools=True,
                supports_streaming=True,
                is_local=False,
                cost_per_1k_tokens=0.003
            )
        ]

    async def check_health(self) -> ProviderHealth:
        if not self.is_available():
            return ProviderHealth(
                provider_id="gemini",
                is_healthy=False,
                status_message="Gemini API key not configured."
            )

        start = time.time()
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=3.5) as client:
                r = await client.get(url)
                latency_ms = (time.time() - start) * 1000.0
                if r.status_code == 200:
                    return ProviderHealth(
                        provider_id="gemini",
                        is_healthy=True,
                        status_message="Online (Authenticated)",
                        latency_ms=round(latency_ms, 2)
                    )
                return ProviderHealth(
                    provider_id="gemini",
                    is_healthy=False,
                    status_message=f"HTTP {r.status_code}",
                    latency_ms=round(latency_ms, 2)
                )
        except Exception as e:
            return ProviderHealth(
                provider_id="gemini",
                is_healthy=False,
                status_message=f"Network error ({type(e).__name__})"
            )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_available():
            raise PermissionError("Gemini API key is not configured.")

        start = time.time()
        model_to_use = request.preferred_model or self.default_model

        parts = []
        if request.system_prompt:
            parts.append({"text": f"System Instructions:\n{request.system_prompt}\n\n"})
        parts.append({"text": request.prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": min(request.max_tokens, 8192)
            }
        }

        url = f"{self.base_url}/models/{model_to_use}:generateContent?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError(f"Empty Gemini response: {data}")

                content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                duration = time.time() - start
                self.record_metrics(duration, success=True)

                usage_meta = data.get("usageMetadata", {})
                return InferenceResponse(
                    content=content,
                    model_used=model_to_use,
                    provider_used="gemini",
                    is_local=False,
                    latency_seconds=duration,
                    token_usage={
                        "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                        "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                        "total_tokens": usage_meta.get("totalTokenCount", 0)
                    }
                )
        except Exception as e:
            duration = time.time() - start
            self.record_metrics(duration, success=False)
            logger.error(f"Gemini generation failed: {e}")
            raise

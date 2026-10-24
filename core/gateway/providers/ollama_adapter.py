"""
core/gateway/providers/ollama_adapter.py
Local Ollama adapter providing strict on-premise inference with zero cloud egress.
"""

import os
import time
import httpx
import logging
from typing import Dict, Any, List, Optional

from core.interfaces.model_gateway import InferenceRequest, InferenceResponse, ModelCapability
from core.gateway.providers.base import BaseProviderAdapter, ProviderHealth

logger = logging.getLogger("OllamaAdapter")


class OllamaAdapter(BaseProviderAdapter):
    def __init__(self, base_url: Optional[str] = None, default_model: str = "llama3.2:1b"):
        super().__init__(provider_id="ollama", is_local=True)
        self.base_url = (base_url or os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.default_model = os.environ.get("LOCAL_MODEL", default_model)

    def is_available(self) -> bool:
        # Check if local endpoint is responding
        try:
            with httpx.Client(timeout=0.8) as client:
                r = client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def get_capabilities(self) -> List[ModelCapability]:
        return [
            ModelCapability(
                provider_id="ollama",
                model_id=self.default_model,
                context_window=8192,
                supports_tools=False,
                supports_streaming=True,
                is_local=True,
                cost_per_1k_tokens=0.0
            )
        ]

    async def check_health(self) -> ProviderHealth:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                latency_ms = (time.time() - start) * 1000.0
                if r.status_code == 200:
                    models = [m.get("name") for m in r.json().get("models", [])]
                    return ProviderHealth(
                        provider_id="ollama",
                        is_healthy=True,
                        status_message=f"Online ({len(models)} models available)",
                        latency_ms=round(latency_ms, 2)
                    )
                return ProviderHealth(
                    provider_id="ollama",
                    is_healthy=False,
                    status_message=f"HTTP {r.status_code}",
                    latency_ms=round(latency_ms, 2)
                )
        except Exception as e:
            return ProviderHealth(
                provider_id="ollama",
                is_healthy=False,
                status_message=f"Offline ({type(e).__name__})"
            )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.time()
        model_to_use = request.preferred_model or self.default_model

        payload = {
            "model": model_to_use,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": min(request.max_tokens, 2048)
            }
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=45.0, write=5.0, pool=5.0)) as client:
                # Discover installed models to avoid 404
                try:
                    tags_r = await client.get(f"{self.base_url}/api/tags", timeout=1.5)
                    if tags_r.status_code == 200:
                        installed = [m.get("name", "") for m in tags_r.json().get("models", [])]
                        if installed and not any(model_to_use in name for name in installed):
                            model_to_use = installed[0]
                            payload["model"] = model_to_use
                except Exception:
                    pass

                r = await client.post(f"{self.base_url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                content = data.get("response", "").strip()
                duration = time.time() - start
                self.record_metrics(duration, success=True)

                return InferenceResponse(
                    content=content,
                    model_used=model_to_use,
                    provider_used="ollama",
                    is_local=True,
                    latency_seconds=duration,
                    token_usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    }
                )
        except Exception as e:
            duration = time.time() - start
            self.record_metrics(duration, success=False)
            logger.error(f"Ollama generation failed: {e}")
            raise

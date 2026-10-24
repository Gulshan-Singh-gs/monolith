"""
core/gateway/router.py
Privacy-enforced Model Gateway routing between Local Ollama, Deterministic Fallback,
Google Gemini, and OpenRouter / Groq.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional

from core.interfaces.model_gateway import (
    IModelProvider,
    PrivacyMode,
    InferenceRequest,
    InferenceResponse
)
from dual_engine_llm import DualEngineLLM

logger = logging.getLogger("ModelGateway")


class SovereignModelGateway:
    def __init__(self, default_privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY):
        self.privacy_mode = default_privacy_mode
        self._legacy_llm = DualEngineLLM()

    def set_privacy_mode(self, mode: PrivacyMode):
        self.privacy_mode = mode
        logger.info(f"ModelGateway privacy mode set to: {mode}")

    def get_privacy_mode(self) -> PrivacyMode:
        return self.privacy_mode

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        """
        Routes inference obeying authoritative privacy policies:
        - LOCAL_ONLY: Strictly Ollama or deterministic local synthesis. Zero cloud egress.
        - HYBRID / CONNECTED: Authorizes configured cloud providers if local inference fails.
        """
        start_time = time.time()
        effective_mode = request.privacy_mode or self.privacy_mode

        # Enforce LOCAL_ONLY boundary
        is_airgap = (
            effective_mode == PrivacyMode.LOCAL_ONLY
            or os.environ.get("AIR_GAP_KILL_SWITCH", "").lower() in ("true", "1", "yes")
        )

        engine_override = "local" if is_airgap else request.preferred_model

        raw_output = await self._legacy_llm.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            engine_override=engine_override,
            air_gap_active=is_airgap
        )

        duration = time.time() - start_time
        used_model = self._legacy_llm.local_model if is_airgap else (request.preferred_model or "auto")

        return InferenceResponse(
            content=str(raw_output),
            model_used=used_model,
            provider_used="ollama_or_local" if is_airgap else "routed_provider",
            is_local=is_airgap,
            latency_seconds=duration,
            token_usage={"approx_tokens": len(str(raw_output).split())}
        )

"""
core/gateway/providers/base.py
Base provider abstraction providing health diagnostics, secret masking, and capability telemetry.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.interfaces.model_gateway import (
    IModelProvider,
    InferenceRequest,
    InferenceResponse,
    ModelCapability
)

logger = logging.getLogger("BaseProvider")


def mask_secret(secret: Optional[str]) -> str:
    """Masks API keys and secrets for secure display and telemetry."""
    if not secret or len(secret) < 8:
        return "********" if secret else "NOT_CONFIGURED"
    return f"{secret[:4]}...{secret[-4:]}"


class ProviderHealth(BaseModel):
    provider_id: str
    is_healthy: bool
    status_message: str
    latency_ms: Optional[float] = None
    checked_at: float = Field(default_factory=time.time)


class BaseProviderAdapter(IModelProvider, ABC):
    def __init__(self, provider_id: str, is_local: bool = False):
        self._provider_id = provider_id
        self._is_local = is_local
        self._request_count = 0
        self._failure_count = 0
        self._total_latency_seconds = 0.0

    def provider_id(self) -> str:
        return self._provider_id

    @property
    def is_local(self) -> bool:
        return self._is_local

    @abstractmethod
    def get_capabilities(self) -> List[ModelCapability]:
        """Returns list of supported models and capability profiles."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Executes a live probe to verify provider availability and latency."""
        pass

    def record_metrics(self, latency: float, success: bool):
        self._request_count += 1
        self._total_latency_seconds += latency
        if not success:
            self._failure_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        avg_latency = (
            (self._total_latency_seconds / self._request_count)
            if self._request_count > 0 else 0.0
        )
        return {
            "provider_id": self._provider_id,
            "is_local": self._is_local,
            "requests_total": self._request_count,
            "failures_total": self._failure_count,
            "avg_latency_seconds": round(avg_latency, 3)
        }

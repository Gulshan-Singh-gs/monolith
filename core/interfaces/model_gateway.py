"""
core/interfaces/model_gateway.py
Abstract model gateway and privacy governance contracts for Sovereign Workbench.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class PrivacyMode(str, Enum):
    LOCAL_ONLY = "LOCAL_ONLY"  # Strict zero-external egress; Ollama and deterministic local only
    HYBRID = "HYBRID"          # Local default; explicitly authorized cloud APIs for non-confidential tasks
    CONNECTED = "CONNECTED"    # Full authorized multi-provider routing with credential isolation


class ModelCapability(BaseModel):
    provider_id: str
    model_id: str
    context_window: int = 4096
    supports_tools: bool = False
    supports_streaming: bool = True
    is_local: bool = False
    cost_per_1k_tokens: float = 0.0


class InferenceRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 4096
    preferred_model: Optional[str] = None
    privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY
    task_classification: str = "general"
    tools: Optional[List[Dict[str, Any]]] = None


class InferenceResponse(BaseModel):
    content: str
    model_used: str
    provider_used: str
    is_local: bool
    latency_seconds: float
    token_usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: str = "stop"


class IModelProvider(ABC):
    @abstractmethod
    def provider_id(self) -> str:
        """Returns unique provider identifier (e.g., 'ollama', 'openrouter', 'gemini', 'groq')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider has required credentials or reachable endpoint."""
        pass

    @abstractmethod
    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Executes inference request obeying privacy and token constraints."""
        pass

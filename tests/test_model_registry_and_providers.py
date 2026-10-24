"""
tests/test_model_registry_and_providers.py
Test suite for ModelProviderRegistry, provider adapters, secret masking,
privacy-enforced routing, and core REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from server import app
from core.gateway.registry import ModelProviderRegistry
from core.gateway.providers.base import mask_secret
from core.interfaces.model_gateway import PrivacyMode, InferenceRequest, ModelCapability
from core.gateway.providers.groq_adapter import GroqAdapter
from core.gateway.providers.grok_adapter import GrokAdapter


def test_secret_masking():
    assert mask_secret("") == "NOT_CONFIGURED"
    assert mask_secret("short") == "********"
    assert mask_secret("gsk_1234567890abcdef") == "gsk_...cdef"


def test_provider_identity_decoupling():
    groq = GroqAdapter(api_key="groq-test-key-123456")
    grok = GrokAdapter(api_key="xai-test-key-123456")

    assert groq.provider_id() == "groq"
    assert grok.provider_id() == "xai_grok"
    assert groq.provider_id() != grok.provider_id()
    assert groq.get_masked_key() != grok.get_masked_key()


@pytest.mark.asyncio
async def test_registry_local_only_boundary_and_fallback():
    registry = ModelProviderRegistry()

    # LOCAL_ONLY mode must NEVER route to cloud providers
    req = InferenceRequest(
        prompt="Analyze workspace security architecture",
        privacy_mode=PrivacyMode.LOCAL_ONLY
    )

    res = await registry.route_inference(req, active_privacy_mode=PrivacyMode.LOCAL_ONLY)
    assert res.is_local is True
    assert res.provider_used in ("ollama", "sovereign_deterministic")
    assert len(res.content) > 0


def test_api_providers_catalog_and_patch_flow(temp_workspace):
    client = TestClient(app)

    # Open workspace
    open_res = client.post("/api/workspace/open", json={"directory_path": str(temp_workspace)})
    assert open_res.status_code == 200

    # 1. Providers endpoint returns masked keys and un-conflated providers
    prov_res = client.get("/api/gateway/providers")
    assert prov_res.status_code == 200
    providers = prov_res.json()["providers"]
    provider_ids = [p["provider_id"] for p in providers]

    assert "ollama" in provider_ids
    assert "groq" in provider_ids
    assert "xai_grok" in provider_ids
    assert "gemini" in provider_ids
    assert "openrouter" in provider_ids

    # Verify no raw secrets exposed in JSON
    for p in providers:
        masked = p["masked_credential"]
        assert "NOT_CONFIGURED" in masked or "..." in masked or "NOT_APPLICABLE" in masked

    # 2. Patch validate API endpoint
    valid_patch = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('Hello Sovereign')\n"
        "+print('Hello Sovereign AI Workbench')\n"
    )
    val_res = client.post("/api/workspace/patch/validate", json={"patch_text": valid_patch})
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True
    assert "main.py" in val_res.json()["affected_files"]

    # 3. Apply patch API endpoint
    apply_res = client.post("/api/workspace/patch/apply", json={"patch_text": valid_patch})
    assert apply_res.status_code == 200
    checkpoint_id = apply_res.json()["checkpoint_id"]
    assert checkpoint_id is not None

    # Verify file updated
    assert "Hello Sovereign AI Workbench" in (temp_workspace / "main.py").read_text(encoding="utf-8")

    # 4. Rollback patch API endpoint
    rb_res = client.post("/api/workspace/patch/rollback", json={"checkpoint_id": checkpoint_id})
    assert rb_res.status_code == 200
    assert rb_res.json()["status"] == "SUCCESS"

    # Verify file reverted
    assert "Hello Sovereign\n" in (temp_workspace / "main.py").read_text(encoding="utf-8")

    # 5. Git status API endpoint
    git_res = client.get("/api/workspace/git/status")
    assert git_res.status_code == 200

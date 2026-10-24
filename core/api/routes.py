"""
core/api/routes.py
FastAPI APIRouter exposing Workspace Engine, Model Gateway, Local Orchestrator,
Skill Registry, and SDLC Artifact Generation.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from core.interfaces.model_gateway import PrivacyMode, InferenceRequest
from core.interfaces.agent import AgentRole, TaskState
from core.workspace.engine import SecureWorkspaceEngine
from core.gateway.router import SovereignModelGateway
from core.orchestrator.orchestrator import LocalOrchestrator
from core.skills.models import SkillCategory, SkillExecutionRequest
from core.skills.registry import SkillRegistry
from core.sdlc.generator import SDLCArtifactGenerator
from core.workspace.patch_engine import PatchEngine
from core.workspace.git_service import GitService

router = APIRouter(prefix="/api", tags=["Sovereign Workbench Core"])

# System Singletons
workspace_engine = SecureWorkspaceEngine(initial_root=Path.cwd())
patch_engine = PatchEngine(workspace_root=workspace_engine.get_root())
git_service = GitService(workspace_root=workspace_engine.get_root(), broker=workspace_engine.execution_broker)
model_gateway = SovereignModelGateway(default_privacy_mode=PrivacyMode.LOCAL_ONLY)
orchestrator = LocalOrchestrator(workspace=workspace_engine, gateway=model_gateway)
skill_registry = SkillRegistry(gateway=model_gateway, workspace=workspace_engine)
sdlc_generator = SDLCArtifactGenerator(workspace=workspace_engine, skill_registry=skill_registry)


@router.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "system": "MONOLITH",
        "version": "2.4.0",
        "architecture": "Autonomous Engineering System",
        "airgap_status": "ACTIVE",
        "sovereign": True
    }



# -------------------------------------------------------------
# WORKSPACE SCHEMAS & ENDPOINTS
# -------------------------------------------------------------
class OpenWorkspaceRequest(BaseModel):
    directory_path: str


class WriteFileRequest(BaseModel):
    relative_path: str
    content: str


class RunCommandRequest(BaseModel):
    command: str
    timeout_seconds: Optional[float] = 30.0


@router.get("/workspace/info")
async def get_workspace_info():
    root = workspace_engine.get_root()
    files = workspace_engine.list_files()
    return {
        "root_path": str(root),
        "name": root.name,
        "total_files": len(files),
        "exists": root.exists()
    }


@router.post("/workspace/open")
async def open_workspace(req: OpenWorkspaceRequest):
    global patch_engine, git_service
    target = Path(req.directory_path).resolve()
    if not target.exists() or not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory '{req.directory_path}' does not exist or is not a directory.")
    success = workspace_engine.set_root(target)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to initialize workspace root.")
    patch_engine = PatchEngine(workspace_root=workspace_engine.get_root())
    git_service = GitService(workspace_root=workspace_engine.get_root(), broker=workspace_engine.execution_broker)
    return {
        "status": "SUCCESS",
        "root_path": str(workspace_engine.get_root()),
        "name": target.name
    }


@router.get("/workspace/files")
async def list_workspace_files(sub_dir: str = ""):
    try:
        files = workspace_engine.list_files(sub_dir=sub_dir)
        return {"files": [f.model_dump() for f in files]}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/file")
async def read_workspace_file(path: str):
    try:
        content = workspace_engine.read_file(path)
        return {"path": path, "content": content}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/file")
async def write_workspace_file(req: WriteFileRequest):
    try:
        workspace_engine.write_file(req.relative_path, req.content)
        return {"status": "SUCCESS", "path": req.relative_path}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/command")
async def run_workspace_command(req: RunCommandRequest):
    res = await workspace_engine.run_command(req.command, timeout_seconds=req.timeout_seconds or 30.0)
    return res.model_dump()


# -------------------------------------------------------------
# PATCH ENGINE & GIT SERVICE ENDPOINTS
# -------------------------------------------------------------
class PatchTextRequest(BaseModel):
    patch_text: str


class RollbackRequest(BaseModel):
    checkpoint_id: str


@router.post("/workspace/patch/validate")
async def validate_patch(req: PatchTextRequest):
    res = patch_engine.validate_patch(req.patch_text)
    return res.model_dump()


@router.post("/workspace/patch/apply")
async def apply_patch(req: PatchTextRequest):
    res = patch_engine.apply_patch(req.patch_text)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.error)
    return res.model_dump()


@router.post("/workspace/patch/rollback")
async def rollback_patch(req: RollbackRequest):
    success = patch_engine.rollback_checkpoint(req.checkpoint_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Checkpoint '{req.checkpoint_id}' not found or rollback failed.")
    return {"status": "SUCCESS", "checkpoint_id": req.checkpoint_id}


@router.get("/workspace/git/status")
async def get_git_status():
    res = await git_service.get_status()
    return res.model_dump()


@router.get("/workspace/git/diff")
async def get_git_diff(staged: bool = False, file_path: Optional[str] = None):
    diff = await git_service.get_diff(staged=staged, file_path=file_path)
    return {"diff": diff}


# -------------------------------------------------------------
# GATEWAY & PRIVACY ENDPOINTS
# -------------------------------------------------------------
class SetPrivacyRequest(BaseModel):
    mode: str


@router.get("/gateway/privacy")
async def get_privacy_mode():
    return {"privacy_mode": model_gateway.get_privacy_mode().value}


@router.post("/gateway/privacy")
async def set_privacy_mode(req: SetPrivacyRequest):
    try:
        mode_enum = PrivacyMode(req.mode.upper())
        model_gateway.set_privacy_mode(mode_enum)
        return {"status": "SUCCESS", "privacy_mode": mode_enum.value}
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid privacy mode '{req.mode}'. Choose from: LOCAL_ONLY, HYBRID, CONNECTED"
        )


@router.get("/gateway/providers")
async def get_gateway_providers():
    return {"providers": model_gateway.list_providers()}


@router.get("/gateway/providers/health")
async def get_gateway_providers_health():
    health = await model_gateway.check_providers_health()
    return {"health": health}


# -------------------------------------------------------------
# ORCHESTRATOR TASK ENDPOINTS
# -------------------------------------------------------------
class CreateTaskRequest(BaseModel):
    role: str
    objective: str
    inputs: Optional[Dict[str, Any]] = None
    requires_approval: Optional[bool] = False


@router.get("/orchestrator/tasks")
async def list_orchestrator_tasks():
    tasks = orchestrator.list_tasks()
    return {"tasks": [t.model_dump() for t in tasks]}


@router.post("/orchestrator/tasks")
async def create_orchestrator_task(req: CreateTaskRequest):
    try:
        role_enum = AgentRole.from_string(req.role)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    task = orchestrator.create_task(
        role=role_enum,
        objective=req.objective,
        inputs=req.inputs or {},
        requires_approval=bool(req.requires_approval)
    )
    return task.model_dump()


@router.get("/orchestrator/tasks/{task_id}")
async def get_orchestrator_task(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump()


@router.post("/orchestrator/tasks/{task_id}/execute")
async def execute_orchestrator_task(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    res = await orchestrator.execute_task(task_id)
    return res.model_dump()


# -------------------------------------------------------------
# SKILLS & SDLC ENDPOINTS
# -------------------------------------------------------------
class ExecuteSkillApiRequest(BaseModel):
    skill_id: str
    parameters: Optional[Dict[str, Any]] = None


class GenerateSDLCRequest(BaseModel):
    product_name: str
    product_description: str
    technical_stack: Optional[str] = "Python, FastAPI, Playwright, Modern CSS"


@router.get("/skills")
async def list_skills(category: Optional[str] = None):
    cat_enum = None
    if category:
        try:
            cat_enum = SkillCategory(category.lower())
        except ValueError:
            pass
    skills = skill_registry.list_skills(category=cat_enum)
    return {"skills": [s.model_dump() for s in skills]}


@router.post("/skills/execute")
async def execute_skill(req: ExecuteSkillApiRequest):
    res = await skill_registry.execute_skill(SkillExecutionRequest(
        skill_id=req.skill_id,
        parameters=req.parameters or {}
    ))
    return res.model_dump()


@router.post("/sdlc/generate")
async def generate_sdlc(req: GenerateSDLCRequest):
    res = await sdlc_generator.generate_sdlc_pack(
        product_name=req.product_name,
        product_description=req.product_description,
        technical_stack=req.technical_stack or "Python, FastAPI, Playwright"
    )
    return res

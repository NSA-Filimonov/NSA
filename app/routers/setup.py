import json
import os
from typing import Literal
from uuid import uuid4
import redis.asyncio as redis
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.validation import parse_grid_size, validate_steps, validate_user_id
router = APIRouter()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
SETUP_TTL_SEC = 600  # 10 минут
class SetupStartRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
class SetupStartResponse(BaseModel):
    setup_session_id: str
class Step(BaseModel):
    cell_a: str
    op: Literal["+", "-", "*"]
    cell_b: str
class SetupSecretRequest(BaseModel):
    setup_session_id: str
    user_id: str
    grid_size: Literal["2x2", "3x3"]
    steps: list[Step]
class SetupSecretResponse(BaseModel):
    status: Literal["ok"]
def _k_setup(session_id: str) -> str:
    return f"nsa:setup:{session_id}"
def _k_secret(user_id: str) -> str:
    return f"nsa:secret:{user_id}"
@router.post("/setup/start", response_model=SetupStartResponse)
async def setup_start(payload: SetupStartRequest):
    user_id = validate_user_id(payload.user_id)
    session_id = str(uuid4())
    await redis_client.set(_k_setup(session_id), json.dumps({"user_id": user_id}), ex=SETUP_TTL_SEC)
    return SetupStartResponse(setup_session_id=session_id)
@router.post("/setup/secret", response_model=SetupSecretResponse)
async def setup_secret(payload: SetupSecretRequest):
    user_id = validate_user_id(payload.user_id)
    raw = await redis_client.get(_k_setup(payload.setup_session_id))
    if not raw:
        raise HTTPException(status_code=400, detail="invalid_setup_session")
    setup_data = json.loads(raw)
    if setup_data.get("user_id") != user_id:
        raise HTTPException(status_code=400, detail="invalid_setup_session")
    rows, cols = parse_grid_size(payload.grid_size)
    normalized_steps = validate_steps([s.dict() for s in payload.steps], rows, cols)
    secret_profile = {
        "grid_size": payload.grid_size,
        "steps": normalized_steps,
    }
    await redis_client.set(_k_secret(user_id), json.dumps(secret_profile))
    await redis_client.delete(_k_setup(payload.setup_session_id))
    return SetupSecretResponse(status="ok")

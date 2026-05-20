import json
import os
import random
from typing import Literal
from uuid import uuid4
import redis.asyncio as redis
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.validation import (
    cell_to_idx,
    parse_grid_size,
    validate_context,
    validate_response_digits,
    validate_steps,
    validate_user_id,
)
router = APIRouter()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
CHALLENGE_TTL_SEC = 120
LOCK_TTL_SEC = 60
FAIL_WINDOW_SEC = 3600
MAX_FAILS = 3
class ChallengeCreateRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    context: str | None = None
class ChallengeCreateResponse(BaseModel):
    challenge_id: str
    grid_values: list[list[int]]
    expires_in_sec: int
class ChallengeVerifyRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    challenge_id: str = Field(min_length=1)
    response: str = Field(min_length=1)
class ChallengeVerifyResponse(BaseModel):
    result: Literal["success", "failed", "locked"]
    reason: str | None = None
    lock_remaining_sec: int | None = None
def _k_secret(user_id: str) -> str:
    return f"nsa:secret:{user_id}"
def _k_challenge(challenge_id: str) -> str:
    return f"nsa:challenge:{challenge_id}"
def _k_fail(user_id: str) -> str:
    return f"nsa:fail:{user_id}"
def _k_lock(user_id: str) -> str:
    return f"nsa:lock:{user_id}"
def _eval_step(a: int, op: str, b: int) -> int:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    raise ValueError("invalid_op")
def _compute_expected_response(grid: list[list[int]], steps: list[dict]) -> str:
    results: list[int] = []
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for s in steps:
        ra, ca = cell_to_idx(s["cell_a"])
        rb, cb = cell_to_idx(s["cell_b"])
        if ra >= rows or rb >= rows or ca >= cols or cb >= cols:
            raise ValueError("invalid_cell_bounds")
        val = _eval_step(grid[ra][ca], s["op"], grid[rb][cb])
        results.append(val)
    if len(results) == 1:
        return str(results[0])
    return "".join(str(abs(x)) for x in results)
@router.post("/challenge/create", response_model=ChallengeCreateResponse)
async def challenge_create(payload: ChallengeCreateRequest):
    user_id = validate_user_id(payload.user_id)
    _ = validate_context(payload.context)
    raw_secret = await redis_client.get(_k_secret(user_id))
    if not raw_secret:
        raise HTTPException(status_code=400, detail="secret_not_configured")
    secret = json.loads(raw_secret)
    rows, cols = parse_grid_size(secret["grid_size"])
    normalized_steps = validate_steps(secret["steps"], rows, cols)
    grid = [[random.randint(1, 9) for _ in range(cols)] for _ in range(rows)]
    try:
        expected_response = _compute_expected_response(grid, normalized_steps)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    challenge_id = str(uuid4())
    challenge_payload = {
        "user_id": user_id,
        "expected_response": expected_response,
    }
    await redis_client.set(
        _k_challenge(challenge_id),
        json.dumps(challenge_payload),
        ex=CHALLENGE_TTL_SEC,
    )
    return ChallengeCreateResponse(
        challenge_id=challenge_id,
        grid_values=grid,
        expires_in_sec=CHALLENGE_TTL_SEC,
    )
@router.post("/challenge/verify", response_model=ChallengeVerifyResponse)
async def challenge_verify(payload: ChallengeVerifyRequest):
    user_id = validate_user_id(payload.user_id)
    response = validate_response_digits(payload.response)
    lock_ttl = await redis_client.ttl(_k_lock(user_id))
    if lock_ttl and lock_ttl > 0:
        return ChallengeVerifyResponse(
            result="locked",
            reason="user_locked",
            lock_remaining_sec=lock_ttl,
        )
    raw_challenge = await redis_client.getdel(_k_challenge(payload.challenge_id))
    if not raw_challenge:
        return ChallengeVerifyResponse(
            result="failed",
            reason="challenge_not_found_or_used",
        )
    challenge = json.loads(raw_challenge)
    if challenge.get("user_id") != user_id:
        return ChallengeVerifyResponse(
            result="failed",
            reason="challenge_user_mismatch",
        )
    expected = str(challenge["expected_response"])
    if response == expected:
        await redis_client.delete(_k_fail(user_id))
        return ChallengeVerifyResponse(result="success")
    fails = await redis_client.incr(_k_fail(user_id))
    ttl = await redis_client.ttl(_k_fail(user_id))
    if ttl is None or ttl < 0:
        await redis_client.expire(_k_fail(user_id), FAIL_WINDOW_SEC)
    if fails >= MAX_FAILS:
        await redis_client.set(_k_lock(user_id), "1", ex=LOCK_TTL_SEC)
        return ChallengeVerifyResponse(
            result="locked",
            reason="too_many_attempts",
            lock_remaining_sec=LOCK_TTL_SEC,
        )
    return ChallengeVerifyResponse(result="failed", reason="invalid_response")

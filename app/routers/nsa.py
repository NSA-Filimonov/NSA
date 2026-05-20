# Copyright 2024 Egor Filimonov, filimoneg@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://apache.org
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# app/routers/nsa.py
from fastapi import APIRouter, HTTPException
from app.schemas.nsa import (
    SetupStartRequest,
    SetupSecretRequest,
    ChallengeCreateRequest,
    ChallengeVerifyRequest,
)
from app.services.nsa_service import NSAService
router = APIRouter()
svc = NSAService()
@router.post("/setup/start")
def setup_start(req: SetupStartRequest):
    return svc.setup_start(req.user_id)
@router.post("/setup/secret")
def setup_secret(req: SetupSecretRequest):
    return svc.setup_secret(req)
@router.post("/challenge/create")
def challenge_create(req: ChallengeCreateRequest):
    try:
        return svc.challenge_create(req.user_id, req.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/challenge/verify")
def challenge_verify(req: ChallengeVerifyRequest):
    try:
        return svc.challenge_verify(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.get("/status")
def status(user_id: str):
    return svc.status(user_id)
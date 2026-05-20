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
# app/schemas/nsa.py
from typing import Literal, List
from pydantic import BaseModel, Field
GridSize = Literal["2x2", "3x2", "3x3", "4x3", "4x4"]
Op = Literal["+", "-", "*"]
class Step(BaseModel):
    cell_a: str
    op: Op
    cell_b: str
class SetupStartRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
class SetupSecretRequest(BaseModel):
    setup_session_id: str
    user_id: str
    grid_size: GridSize
    steps: List[Step]
class ChallengeCreateRequest(BaseModel):
    user_id: str
    context: str = "app_login"
class ChallengeVerifyRequest(BaseModel):
    user_id: str
    challenge_id: str
    response: str
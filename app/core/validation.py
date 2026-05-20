#Copyright 2024 Egor Filimonov, filimoneg@gmail.com
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
# /home/filimor/NSA/nsa-backend-v1.1/app/core/validation.py
import re
from typing import Iterable, Mapping, Tuple
from fastapi import HTTPException
# --- Ограничения/политики ---
ALLOWED_GRID_SIZES = {"2x2", "3x3"}
ALLOWED_OPS = {"+", "-", "*"}
USER_ID_RE = re.compile(r"^[a-zA-Z0-9._@:-]{1,128}$")
CELL_RE = re.compile(r"^[A-Z][1-9]\d*$")
DIGITS_RE = re.compile(r"^\d{1,12}$")
MAX_STEPS = 8
MAX_CONTEXT_LEN = 256
def _bad_request(detail: str) -> HTTPException:
    # Единый формат ошибок валидации для ваших роутов
    return HTTPException(status_code=400, detail=detail)
def validate_user_id(user_id: str) -> str:
    if not isinstance(user_id, str):
        raise _bad_request("user_id_must_be_string")
    user_id = user_id.strip()
    if not USER_ID_RE.fullmatch(user_id):
        raise _bad_request("invalid_user_id")
    return user_id
def validate_context(context: str | None) -> str | None:
    if context is None:
        return None
    if not isinstance(context, str):
        raise _bad_request("context_must_be_string")
    if len(context) > MAX_CONTEXT_LEN:
        raise _bad_request("context_too_long")
    return context
def parse_grid_size(grid_size: str) -> Tuple[int, int]:
    if not isinstance(grid_size, str):
        raise _bad_request("grid_size_must_be_string")
    grid_size = grid_size.strip().lower()
    if grid_size not in ALLOWED_GRID_SIZES:
        raise _bad_request("invalid_grid_size")
    r_str, c_str = grid_size.split("x")
    return int(r_str), int(c_str)
def normalize_cell(cell: str) -> str:
    if not isinstance(cell, str):
        raise _bad_request("cell_must_be_string")
    cell = cell.strip().upper()
    if not CELL_RE.fullmatch(cell):
        raise _bad_request("invalid_cell_format")
    return cell
def cell_to_idx(cell: str) -> Tuple[int, int]:
    cell = normalize_cell(cell)
    row = ord(cell[0]) - ord("A")
    col = int(cell[1:]) - 1
    return row, col
def ensure_cell_in_bounds(cell: str, rows: int, cols: int) -> str:
    norm = normalize_cell(cell)
    r, c = cell_to_idx(norm)
    if not (0 <= r < rows and 0 <= c < cols):
        raise _bad_request("cell_out_of_bounds")
    return norm
def validate_steps(steps: Iterable[Mapping], rows: int, cols: int) -> list[dict]:
    if steps is None:
        raise _bad_request("steps_required")
    steps_list = list(steps)
    if not steps_list:
        raise _bad_request("steps_required")
    if len(steps_list) > MAX_STEPS:
        raise _bad_request("too_many_steps")
    normalized: list[dict] = []
    for idx, step in enumerate(steps_list):
        if not isinstance(step, Mapping):
            raise _bad_request(f"invalid_step_type_at_{idx}")
        try:
            cell_a = ensure_cell_in_bounds(step["cell_a"], rows, cols)
            op = step["op"]
            cell_b = ensure_cell_in_bounds(step["cell_b"], rows, cols)
        except KeyError:
            raise _bad_request(f"missing_step_field_at_{idx}")
        if op not in ALLOWED_OPS:
            raise _bad_request(f"invalid_step_op_at_{idx}")
        normalized.append({"cell_a": cell_a, "op": op, "cell_b": cell_b})
    return normalized
def validate_response_digits(response: str) -> str:
    if not isinstance(response, str):
        raise _bad_request("response_must_be_string")
    response = response.strip()
    # Совместимо с вашим smoke: нецифровой ответ должен давать 400
    if not DIGITS_RE.fullmatch(response):
        raise _bad_request("response_digits_only")
    return response
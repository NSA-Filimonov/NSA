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
from fastapi import FastAPI
from app.core.config import is_production
from app.routers.auth import router as auth_router
from app.routers.setup import router as setup_router
from app.routers.status import router as status_router
prod = is_production()
app = FastAPI(
    title="NSA Backend v1.1",
    version="1.1.0",
    docs_url=None if prod else "/docs",
    redoc_url=None if prod else "/redoc",
    openapi_url=None if prod else "/openapi.json",
)
app.include_router(setup_router, prefix="/nsa", tags=["setup"])
app.include_router(auth_router, prefix="/nsa", tags=["auth"])
app.include_router(status_router, prefix="/nsa", tags=["status"])
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import engine
from .models import Base
from .routers import api_keys, auth, capture, endpoints, forwarding, organizations, replays, requests
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
app = FastAPI(title="RequestBinX", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","), allow_credentials=False, allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"], allow_headers=["Authorization","Content-Type"])
app.include_router(auth.router); app.include_router(requests.router); app.include_router(endpoints.router); app.include_router(capture.router); app.include_router(replays.router); app.include_router(api_keys.router); app.include_router(organizations.router); app.include_router(forwarding.router)
@app.on_event("startup")
async def startup():
    async with engine.begin() as connection: await connection.run_sync(Base.metadata.create_all)
@app.get("/healthz")
async def healthz(): return {"status":"ok"}
@app.get("/readyz")
async def readyz(): return {"status":"ready"}

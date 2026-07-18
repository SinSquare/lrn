"""HTTP route modules."""

from fastapi import APIRouter

from lrn.routes import dashboard, process, prompts, samples

api_router = APIRouter()
api_router.include_router(prompts.router)
api_router.include_router(samples.router)
api_router.include_router(process.router)
api_router.include_router(dashboard.router)

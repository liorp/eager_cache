from fastapi.routing import APIRouter

from eager_cache.web.api import data, docs, monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(docs.router)
api_router.include_router(data.router, prefix="/data", tags=["data"])

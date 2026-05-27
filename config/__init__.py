from fastapi import FastAPI
from app.api.api_responser import ApiResponser
from config.settings.base import connect_db
from fastapi.middleware.cors import CORSMiddleware

def create_app():
    app = FastAPI(
        title="ms-optimization microservice",
        version="v1"
    )

    """
    Initialize URLs
    """
    import app.api.meta.views as meta
    import app.api.v1.views as api

    app.include_router(meta.router, tags=["meta"])
    app.include_router(api.router, tags=["core"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return ApiResponser.error(str(exc), 500)

    app.add_event_handler(
        "startup",
        connect_db
    )

    return app

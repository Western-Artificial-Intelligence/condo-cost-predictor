from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .routers import neighbourhoods, predict

def create_app() -> FastAPI:
    app = FastAPI(
        title="Condo Cost Predictor API",
        version="0.1.0",
        description="API for Toronto condo affordability predictions and metadata."
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(neighbourhoods.router, prefix=settings.API_PREFIX, tags=["neighbourhoods"])
    app.include_router(predict.router,       prefix=settings.API_PREFIX, tags=["predict"])

    @app.get("/")
    def root():
        return {"ok": True, "service": "condo-cost-predictor-api"}

    return app

app = create_app()

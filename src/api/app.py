from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import Settings, get_settings
from src.domain.exceptions import AgronomyEngineError
from src.api.routes import health, telemetry, recommendation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup directories on startup
    settings = get_settings()
    settings.ensure_directories()
    yield
    # Teardown logic if needed


def create_app() -> FastAPI:
    """Application factory for the IoT Crop Recommendation REST service."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Production-grade AI Engineering system recommending optimal crops "
            "and precision cultivation strategies based on IoT telemetry and FAO EcoCrop."
        ),
        lifespan=lifespan
    )

    # Enable CORS for frontend dashboard and mobile client integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global domain exception handler
    @app.exception_handler(AgronomyEngineError)
    async def handle_domain_error(request: Request, exc: AgronomyEngineError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": exc.__class__.__name__, "message": str(exc)}
        )

    # Register API routers
    app.include_router(health.router)
    app.include_router(telemetry.router, prefix="/api/v1")
    app.include_router(recommendation.router, prefix="/api/v1")

    # Serve built Frontend UI seamlessly at root URL
    fe_dist = settings.base_dir / "FE" / "dist"
    if fe_dist.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(fe_dist), html=True), name="frontend")

    return app


app = create_app()

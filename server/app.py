"""
server/app.py

FastAPI app factory. Binds to 127.0.0.1 only (see server/main.py), CORS
restricted to the Vite dev origin, and in production mode serves the built
web/dist SPA directly so a single process ("make start") is all that's
needed.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server import config as server_config
from server.routers import benchmark, config as config_router, health, presets, runs, stats

WEB_DIST = server_config.REPO_ROOT / "web" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="PhishForge Console API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_config.DEV_CORS_ORIGINS,
        allow_methods=["GET", "POST", "DELETE", "PUT"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(config_router.router, prefix="/api")
    app.include_router(presets.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(benchmark.router, prefix="/api")

    if WEB_DIST.exists():
        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str) -> FileResponse:
            candidate = WEB_DIST / full_path
            if full_path and candidate.exists() and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(WEB_DIST / "index.html")

    return app


app = create_app()

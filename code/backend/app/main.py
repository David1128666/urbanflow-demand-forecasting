from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import API_CORS_ORIGINS, APP_DESCRIPTION, APP_TITLE
from app.locales import translate
from app.routers import (
    dashboard,
    demand,
    dispatch,
    forecasts,
    inventory,
    models,
    stations,
)
from app.services.health_service import get_health


app = FastAPI(
    title=APP_TITLE,
    version=__version__,
    description=APP_DESCRIPTION,
    openapi_tags=[
        {
            "name": translate("tags.system"),
            "description": translate("route.health.description"),
        },
        {
            "name": translate("tags.stations"),
            "description": translate("route.stations.list"),
        },
        {
            "name": translate("tags.demand"),
            "description": translate("route.demand.history"),
        },
        {
            "name": translate("tags.forecasts"),
            "description": translate("route.forecasts.latest"),
        },
        {
            "name": translate("tags.models"),
            "description": translate("route.models.metrics"),
        },
        {
            "name": translate("tags.dashboard"),
            "description": translate("route.dashboard.summary"),
        },
        {
            "name": translate("tags.inventory"),
            "description": translate("route.inventory.latest"),
        },
        {
            "name": translate("tags.dispatch"),
            "description": translate("route.dispatch.summary"),
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(stations.router)
app.include_router(demand.router)
app.include_router(forecasts.router)
app.include_router(models.router)
app.include_router(dashboard.router)
app.include_router(inventory.router)
app.include_router(dispatch.router)


@app.get(
    "/",
    tags=[translate("tags.system")],
    summary=translate("route.root.summary"),
    description=translate("route.root.description"),
)
def root() -> dict[str, str]:
    return {
        "name": translate("app.name"),
        "version": __version__,
        "status": translate("app.running"),
    }


@app.get(
    "/health",
    tags=[translate("tags.system")],
    summary=translate("route.health.summary"),
    description=translate("route.health.description"),
)
def health() -> JSONResponse:
    payload = get_health()
    status_code = 503 if payload["status"] == "unavailable" else 200
    return JSONResponse(status_code=status_code, content=payload)

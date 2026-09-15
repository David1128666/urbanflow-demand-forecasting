from fastapi import APIRouter, Query

from app.locales import translate
from app.responses import success
from app.services.dispatch_service import (
    get_dispatch_recommendations,
    get_dispatch_summary,
)


router = APIRouter(
    prefix="/api/v1/dispatch",
    tags=[translate("tags.dispatch")],
)


@router.get("/summary", summary=translate("route.dispatch.summary"))
def dispatch_summary():
    return success(get_dispatch_summary())


@router.get(
    "/recommendations",
    summary=translate("route.dispatch.recommendations"),
)
def dispatch_recommendations(
    limit: int = Query(100, ge=1, le=500),
):
    return success(get_dispatch_recommendations(limit))

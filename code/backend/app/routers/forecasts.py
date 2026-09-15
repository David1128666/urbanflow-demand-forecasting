from fastapi import APIRouter, Query

from app.locales import translate
from app.responses import success
from app.services.forecast_service import get_latest_forecasts


router = APIRouter(
    prefix="/api/v1/forecasts",
    tags=[translate("tags.forecasts")],
)


@router.get("/latest", summary=translate("route.forecasts.latest"))
def latest_forecasts(
    station_id: str | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
):
    result = get_latest_forecasts(station_id=station_id, limit=limit)
    return success(result)

from datetime import datetime

from fastapi import APIRouter, Query

from app.locales import translate
from app.responses import success
from app.services.demand_service import get_demand_history


router = APIRouter(
    prefix="/api/v1/demand",
    tags=[translate("tags.demand")],
)


@router.get("/history", summary=translate("route.demand.history"))
def history(
    station_id: str = Query(...),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
):
    rows = get_demand_history(
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return success(
        {
            "station_id": station_id,
            "count": len(rows),
            "points": rows,
        }
    )

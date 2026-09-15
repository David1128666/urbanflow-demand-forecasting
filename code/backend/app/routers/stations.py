from fastapi import APIRouter, HTTPException, Query

from app.locales import translate
from app.responses import success
from app.services.station_service import get_station, list_stations


router = APIRouter(
    prefix="/api/v1/stations",
    tags=[translate("tags.stations")],
)


@router.get("", summary=translate("route.stations.list"))
def stations(
    city_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return success(list_stations(city_id, limit, offset))


@router.get("/{station_id}", summary=translate("route.stations.detail"))
def station_detail(station_id: str):
    station = get_station(station_id)
    if station is None:
        raise HTTPException(
            status_code=404,
            detail=translate("station.not_found"),
        )
    return success(station)

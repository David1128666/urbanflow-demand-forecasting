from fastapi import APIRouter, Query

from app.locales import translate
from app.responses import success
from app.services.inventory_service import get_latest_inventory


router = APIRouter(
    prefix="/api/v1/inventory",
    tags=[translate("tags.inventory")],
)


@router.get("/latest", summary=translate("route.inventory.latest"))
def latest_inventory(
    station_id: str | None = Query(None),
):
    return success(get_latest_inventory(station_id))

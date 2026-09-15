from fastapi import APIRouter

from app.locales import translate
from app.responses import success
from app.services.dashboard_service import get_dashboard_summary


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=[translate("tags.dashboard")],
)


@router.get("/summary", summary=translate("route.dashboard.summary"))
def summary():
    return success(get_dashboard_summary())

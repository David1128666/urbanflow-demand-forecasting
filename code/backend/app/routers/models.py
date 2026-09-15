from fastapi import APIRouter, Query

from app.locales import translate
from app.responses import success
from app.services.model_service import get_model_metrics


router = APIRouter(
    prefix="/api/v1/models",
    tags=[translate("tags.models")],
)


@router.get("/metrics", summary=translate("route.models.metrics"))
def metrics(
    include_horizons: bool = Query(False),
):
    return success(get_model_metrics(include_horizons=include_horizons))

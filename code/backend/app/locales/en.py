"""English API and business messages."""

MESSAGES = {
    "app.name": "UrbanFlow Demand Forecasting API",
    "app.running": "running",
    "tags.system": "System",
    "tags.stations": "Stations",
    "tags.demand": "Demand",
    "tags.forecasts": "Forecasts",
    "tags.models": "Models",
    "tags.dashboard": "Dashboard",
    "tags.inventory": "Inventory",
    "tags.dispatch": "Dispatch",
    "route.root.summary": "Service information",
    "route.root.description": "Return the service name, version, and status.",
    "route.health.summary": "Health and data readiness",
    "route.health.description": (
        "Check the API, MySQL connection, latest forecast, inventory, "
        "and dispatch consistency."
    ),
    "route.stations.list": "List stations",
    "route.stations.detail": "Station details",
    "route.demand.history": "Demand history",
    "route.forecasts.latest": "Latest forecast",
    "route.models.metrics": "Model metrics and model card",
    "route.dashboard.summary": "Operations dashboard summary",
    "route.inventory.latest": "Latest station inventory",
    "route.dispatch.summary": "Dispatch summary",
    "route.dispatch.recommendations": "Dispatch recommendations",
    "station.not_found": "Station not found",
    "station_status.empty": "No bikes available",
    "station_status.low": "Low bike availability",
    "station_status.full": "Limited return capacity",
    "station_status.normal": "Normal supply",
    "station_note.empty": "Prioritize replenishment to avoid failed rentals",
    "station_note.low": "Monitor peak demand and replenish when needed",
    "station_note.full": "Prioritize bike collection to preserve return capacity",
    "station_note.normal": "No manual intervention is currently required",
    "operation.status.urgent": "Dispatch now",
    "operation.status.replenish": "Replenishment recommended",
    "operation.status.return_pressure": "Return capacity pressure",
    "operation.status.normal": "Normal supply",
    "operation.action.no_inventory": (
        "No inventory snapshot is available, so a replenishment quantity "
        "cannot be calculated."
    ),
    "operation.action.replenish": (
        "Expected ride orders in the next 2 hours: {demand:.0f}. "
        "Available bikes: {available}. Target stock: {target}. "
        "Move {quantity} bikes before {deadline}."
    ),
    "operation.action.return_pressure": (
        "Available bikes: {available}. Available docks: {docks}. "
        "Return capacity is tight; collect bikes or add temporary capacity."
    ),
    "operation.action.normal": (
        "Available bikes: {available}. Target stock: {target}. "
        "No manual replenishment is needed in the next 2 hours."
    ),
    "operation.demand_unit": "ride orders",
    "dispatch.result_basis": (
        "Simulation based on virtual inventory and forecast data; this is "
        "not a realized operating benefit."
    ),
    "dispatch.status.pending": "Pending",
    "dispatch.priority.critical": "Critical",
    "dispatch.priority.high": "High",
    "dispatch.priority.medium": "Medium",
    "dispatch.priority.low": "Low",
    "dispatch.action_text": (
        "Move {quantity} bikes from {source} to {target} before {deadline}."
    ),
    "dispatch.reason": (
        "Expected ride orders in the next 120 minutes: {demand:.0f}. "
        "Available bikes: {available}. Target stock: {target}."
    ),
    "dashboard.data_mode_label": "Virtual demo data",
    "dashboard.business_definition": (
        "Demand is the expected number of ride orders in each 30-minute "
        "window. Dispatch recommendations use the next 2 hours of demand, "
        "current available bikes, and safety stock."
    ),
    "dashboard.consistency.ready": (
        "Forecast, inventory, and dispatch data use the same run."
    ),
    "dashboard.consistency.missing_forecast": (
        "No successful forecast run is available."
    ),
    "dashboard.consistency.missing_inventory": (
        "No inventory snapshot is available."
    ),
    "dashboard.consistency.missing_dispatch": (
        "Forecast data exists, but dispatch recommendations have not been "
        "generated."
    ),
    "dashboard.consistency.stale_dispatch": (
        "Dispatch recommendations were generated for an older forecast run."
    ),
    "dashboard.consistency.updating": (
        "A new forecast is available and dispatch recommendations are being "
        "refreshed."
    ),
}

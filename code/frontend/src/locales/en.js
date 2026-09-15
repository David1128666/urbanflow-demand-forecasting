export default {
  "nav.overview": "Overview",
  "nav.forecast": "Forecast",
  "nav.models": "Models",
  "nav.dispatch": "Dispatch",
  "nav.docs": "API Docs",
  "language.switch": "中文",

  "common.refresh": "Refresh",
  "common.requestFailed": "Request failed",
  "common.noData": "No data available",
  "common.to": "to",
  "common.bikes": "bikes",
  "common.orders": "orders",
  "common.jobs": "work orders",
  "common.minutes": "minutes",
  "common.status.checking": "Checking",
  "common.status.online": "Online",
  "common.status.degraded": "Degraded",
  "common.status.offline": "Offline",
  "common.status.unknown": "Unknown",
  "common.priority.critical": "Critical",
  "common.priority.high": "High",
  "common.priority.medium": "Medium",
  "common.priority.low": "Low",
  "common.status.pending": "Pending",
  "common.validation": "Validation",
  "common.test": "Test",

  "home.eyebrow": "Urban demand forecasting",
  "home.title": "Operations Overview",
  "home.subtitle":
    "Translate station-level forecasts into actions: where to move bikes, how many, and when.",
  "home.dataMode": "Virtual demo data",
  "home.metric.stations": "Stations in operation",
  "home.metric.stationsHelp": "Every station has an independent forecast",
  "home.metric.twoHourOrders": "Expected orders in 2 hours",
  "home.metric.twoHourOrdersHelp": "Sum of four 30-minute windows",
  "home.metric.intervention": "Stations needing intervention",
  "home.metric.interventionHelp":
    "Available bikes are below the target stock",
  "home.metric.recommendedMoves": "Recommended bike moves",
  "home.metric.recommendedMovesHelp":
    "Split into {count} dispatch work orders",
  "home.ranking.title": "Station demand ranking",
  "home.ranking.axis": "Expected ride orders",
  "home.ranking.subtitle":
    "Cumulative ride orders over the next 24 hours for capacity planning.",
  "home.peak.title": "Demand peak windows",
  "home.peak.axis": "Orders per 30 minutes",
  "home.peak.subtitle":
    "City-wide orders in each 30-minute window, useful for staffing decisions.",
  "home.dispatch.title": "Dispatch impact simulation",
  "home.dispatch.subtitle":
    "Simulate how the identified shortage changes if all recommendations are executed.",
  "home.dispatch.view": "View dispatch plan",
  "home.dispatch.window": "Decision window",
  "home.dispatch.riskOrders": "Orders at risk",
  "home.dispatch.workOrders": "Dispatch work orders",
  "home.dispatch.remainingRisk": "Remaining risk after simulation",
  "home.dispatch.reduction": "Simulated shortage reduction",
  "home.consistency.ready":
    "Forecast, inventory, and dispatch data use the same run.",
  "home.consistency.missing_forecast":
    "No successful forecast run is available.",
  "home.consistency.missing_inventory":
    "No inventory snapshot is available.",
  "home.consistency.missing_dispatch":
    "Forecast data exists, but dispatch recommendations have not been generated.",
  "home.consistency.stale_dispatch":
    "Dispatch recommendations were generated for an older forecast run.",
  "home.consistency.updating":
    "A new forecast is available and dispatch recommendations are being refreshed.",
  "home.glossary.title": "What this project solves",
  "home.glossary.subtitle":
    "Every number maps to an operational question instead of a technology metric.",
  "home.glossary.demandTitle": "What is demand?",
  "home.glossary.demandBody":
    "The expected number of ride orders that start at a station during a 30-minute window.",
  "home.glossary.gapTitle": "What is a shortage?",
  "home.glossary.gapBody":
    "The additional available bikes needed to cover near-term demand and keep safety stock.",
  "home.glossary.dispatchTitle": "What is a recommendation?",
  "home.glossary.dispatchBody":
    "A concrete transfer from a surplus station, including quantity, distance, and deadline.",
  "home.glossary.impactTitle": "What is simulated impact?",
  "home.glossary.impactBody":
    "The shortage reduction if every recommendation is executed. It is not realized revenue or benefit.",
  "home.run.title": "Current forecast run",
  "home.run.subtitle": "Latest successful batch written to MySQL.",
  "home.run.id": "Run ID",
  "home.run.cutoff": "Data cutoff",
  "home.run.start": "Forecast start",
  "home.run.steps": "Forecast steps",
  "home.run.generated": "Generated at",
  "home.error": "Dashboard data could not be loaded",

  "forecast.eyebrow": "Demand forecast",
  "forecast.title": "Station Demand for the Next 24 Hours",
  "forecast.subtitle":
    '"Demand" means expected ride orders in each 30-minute window, not riders, revenue, or bike failures.',
  "forecast.metric.nextTwoHours": "Expected orders in 2 hours",
  "forecast.metric.nextTwoHoursHelp":
    "These four windows drive the current dispatch decision",
  "forecast.metric.available": "Available bikes now",
  "forecast.metric.snapshot":
    "Snapshot {time}; capacity {capacity}",
  "forecast.metric.replenishment": "Recommended replenishment",
  "forecast.metric.target":
    "Target stock {target}; safety stock {safety}",
  "forecast.metric.operationStatus": "Operation status",
  "forecast.metric.deadline": "Handle before {time}",
  "forecast.status.urgent": "Dispatch now",
  "forecast.status.replenish": "Replenishment recommended",
  "forecast.status.returnPressure": "Return capacity pressure",
  "forecast.status.normal": "Normal supply",
  "forecast.stationStatus.empty": "No bikes available",
  "forecast.stationStatus.low": "Low bike availability",
  "forecast.stationStatus.full": "Limited return capacity",
  "forecast.stationStatus.normal": "Normal supply",
  "forecast.action.noInventory":
    "No inventory snapshot is available, so replenishment cannot be calculated.",
  "forecast.action.replenish":
    "Expected orders in the next 2 hours: {demand}. Available bikes: {available}. Target stock: {target}. Move {quantity} bikes before {deadline}.",
  "forecast.action.returnPressure":
    "Available bikes: {available}. Available docks: {docks}. Return capacity is tight; collect bikes or add temporary capacity.",
  "forecast.action.normal":
    "Available bikes: {available}. Target stock: {target}. No manual replenishment is needed in the next 2 hours.",
  "forecast.chart.title": "{station} ride-order history and forecast",
  "forecast.chart.history": "Historical ride orders",
  "forecast.chart.forecast": "Forecast ride orders",
  "forecast.chart.yAxis": "Expected ride orders",
  "forecast.chart.subtitle":
    "Data cutoff {cutoff}. Forecast starts at {start}. Each point represents expected ride orders in the following 30 minutes.",
  "forecast.operation.title": "Operational meaning",
  "forecast.operation.subtitle":
    "Convert the forecast into target stock, a deadline, and a responsible action.",
  "forecast.operation.available": "Available bikes",
  "forecast.operation.docks": "Available docks",
  "forecast.operation.stationStatus": "Station status",
  "forecast.operation.peak": "Peak 30-minute demand",
  "forecast.operation.run": "Forecast run",
  "forecast.operation.action": "Recommended action",
  "forecast.operation.noAction": "No executable recommendation",
  "forecast.points.title": "Next 48 forecast points",
  "forecast.points.subtitle":
    "Each row is a verifiable 30-minute demand window and its operational meaning.",
  "forecast.points.count": "{count} points",
  "forecast.table.window": "Forecast window",
  "forecast.table.orders": "Expected ride orders",
  "forecast.table.meaning": "Dispatch implication",
  "forecast.impact.veryHigh":
    "Strong peak; replenish before the window starts",
  "forecast.impact.high":
    "Peak; confirm bike availability in advance",
  "forecast.impact.normal":
    "Regular demand; keep bikes available",
  "forecast.impact.low": "Low demand; routine inspection",
  "forecast.error.stations": "Stations could not be loaded",
  "forecast.error.data": "Forecast data could not be loaded",

  "models.eyebrow": "Model evaluation",
  "models.title": "Model Selection and Metrics",
  "models.subtitle":
    "All models use the same chronological validation and test splits. The 48-step validation MAE selects the production model.",
  "models.current": "Active model",
  "models.name.seasonal": "Seasonal Naive",
  "models.name.tcn": "TCN",
  "models.baselineMae": "Baseline validation MAE",
  "models.tcnMae": "TCN validation MAE",
  "models.experimental": "Challenger model",
  "models.threshold": "Minimum improvement",
  "models.thresholdHelp": "Baseline remains active below this threshold",
  "models.card.title": "Model card",
  "models.card.subtitle":
    "Reproducibility and selection details for the active forecasting model.",
  "models.card.modelType": "Model type",
  "models.card.selectionRule": "Selection rule",
  "models.rule":
    "Choose the model with the lowest 48-step validation MAE. A challenger must improve the baseline by at least 5%.",
  "models.card.improvement": "TCN improvement",
  "models.card.challengerUpdated": "TCN artifact updated",
  "models.card.dataMode": "Data mode",
  "models.card.limitations": "Known limitations",
  "models.type.tcn": "Temporal Convolutional Network (deep learning)",
  "models.type.baseline": "Seasonal Naive (statistical baseline)",
  "models.reason.tcn":
    "TCN improves the baseline by {improvement}%, exceeding the required {required}%.",
  "models.reason.baseline":
    "TCN improvement is {improvement}%, below the required {required}%, so the baseline remains active.",
  "models.limitation.synthetic":
    "The active model is selected using synthetic data.",
  "models.limitation.intervals":
    "Point forecasts are shown without prediction intervals.",
  "models.chart.title": "MAE comparison",
  "models.chart.validationMae": "Validation MAE",
  "models.chart.testMae": "Test MAE",
  "models.chart.subtitle": "Lower is better on validation and test data.",
  "models.table.title": "Metric details",
  "models.table.subtitle": "MAE, RMSE, and sMAPE; sMAPE is a percentage.",
  "models.table.model": "Model",
  "models.table.version": "Version",
  "models.table.dataset": "Dataset",
  "models.error": "Model metrics could not be loaded",

  "dispatch.eyebrow": "Dispatch recommendations",
  "dispatch.title": "Bike Moves and Shortage Reduction",
  "dispatch.subtitle":
    "Convert the next two hours of demand into concrete replenishment actions.",
  "dispatch.scope":
    "A shortage is the number of additional available bikes needed to cover expected orders and safety stock. Risk orders are a conservative demand proxy, not confirmed lost rides. Impact is simulated on virtual data.",
  "dispatch.metric.intervention": "Stations needing intervention",
  "dispatch.metric.risk": "Orders at risk",
  "dispatch.metric.riskHelp":
    "Upper-bound demand exposed to a bike shortage without intervention",
  "dispatch.metric.moves": "Recommended bike moves",
  "dispatch.metric.movesHelp":
    "{count} work orders from {sources} surplus stations",
  "dispatch.metric.reduction": "Simulated risk reduction",
  "dispatch.metric.reductionHelp":
    "Reduces {count} risk units, covering {pct}% of expected two-hour demand",
  "dispatch.queue.title": "Priority action queue",
  "dispatch.queue.subtitle":
    "Start with the most urgent recommendations that affect the most orders.",
  "dispatch.queue.sorted": "Sorted by priority",
  "dispatch.priorityBadge": "{label} priority",
  "dispatch.queue.distance": "Distance {distance} km",
  "dispatch.queue.shortage": "Shortage {before} → {after}",
  "dispatch.queue.lead": "Lead time {minutes} minutes",
  "dispatch.chart.title": "Recommended move quantity",
  "dispatch.chart.axis": "Bikes moved",
  "dispatch.chart.subtitle":
    "The horizontal axis is the number of bikes that must be physically moved.",
  "dispatch.table.title": "Dispatch actions",
  "dispatch.table.subtitle":
    "Each row can become a work order. The expected shortage falls to the post-dispatch value.",
  "dispatch.table.count": "{count} recommendations",
  "dispatch.table.priority": "Priority",
  "dispatch.table.from": "From",
  "dispatch.table.to": "To",
  "dispatch.table.quantity": "Bikes moved",
  "dispatch.table.target": "Target stock",
  "dispatch.table.before": "Shortage before",
  "dispatch.table.after": "Shortage after",
  "dispatch.table.distance": "Distance",
  "dispatch.table.deadline": "Deadline",
  "dispatch.table.reason": "Business reason",
  "dispatch.error": "Dispatch recommendations could not be loaded",
  "dispatch.stale":
    "Dispatch recommendations use an older forecast run. Regenerate them before relying on the numbers.",
  "dispatch.action":
    "Move {quantity} bikes from {source} to {target} before {deadline}.",
  "dispatch.reason":
    "Expected ride orders in the next 120 minutes: {demand}. Available bikes: {available}. Target stock: {target}.",
};

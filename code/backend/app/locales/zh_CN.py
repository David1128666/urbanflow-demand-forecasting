"""Chinese API and business messages preserved for local use."""

MESSAGES = {
    "app.name": "UrbanFlow 城市需求预测 API",
    "app.running": "运行中",
    "tags.system": "系统",
    "tags.stations": "站点",
    "tags.demand": "需求",
    "tags.forecasts": "预测",
    "tags.models": "模型",
    "tags.dashboard": "看板",
    "tags.inventory": "库存",
    "tags.dispatch": "调度",
    "route.root.summary": "服务信息",
    "route.root.description": "返回服务名称、版本和当前运行状态。",
    "route.health.summary": "健康检查与数据就绪状态",
    "route.health.description": (
        "检查 API、MySQL、最新预测、库存和调度建议是否一致。"
    ),
    "route.stations.list": "站点列表",
    "route.stations.detail": "站点详情",
    "route.demand.history": "历史需求",
    "route.forecasts.latest": "最新预测",
    "route.models.metrics": "模型指标与模型卡片",
    "route.dashboard.summary": "看板汇总",
    "route.inventory.latest": "最新站点库存",
    "route.dispatch.summary": "调度建议汇总",
    "route.dispatch.recommendations": "调运建议列表",
    "station.not_found": "站点不存在",
    "station_status.empty": "无车可借",
    "station_status.low": "车辆偏少",
    "station_status.full": "车位紧张",
    "station_status.normal": "供给正常",
    "station_note.empty": "优先补车，避免用户到站无车可借",
    "station_note.low": "关注高峰订单，必要时提前补车",
    "station_note.full": "优先回收车辆，避免用户无法还车",
    "station_note.normal": "当前无需人工干预",
    "operation.status.urgent": "立即调度",
    "operation.status.replenish": "建议补车",
    "operation.status.return_pressure": "还车压力",
    "operation.status.normal": "供给正常",
    "operation.action.no_inventory": (
        "当前没有库存快照，暂无法生成补车数量。"
    ),
    "operation.action.replenish": (
        "未来 2 小时预计有 {demand:.0f} 笔骑行订单；"
        "当前可借 {available} 辆，目标备车 {target} 辆，"
        "建议在 {deadline} 前补车 {quantity} 辆。"
    ),
    "operation.action.return_pressure": (
        "当前可借 {available} 辆、空桩 {docks} 个，"
        "还车压力较高，建议优先回收车辆或增加临时停车位。"
    ),
    "operation.action.normal": (
        "当前可借 {available} 辆，目标备车 {target} 辆，"
        "未来 2 小时暂不需要人工补车。"
    ),
    "operation.demand_unit": "骑行订单",
    "dispatch.result_basis": (
        "基于虚拟库存与预测数据的模拟，尚未代表真实运营收益。"
    ),
    "dispatch.status.pending": "待执行",
    "dispatch.priority.critical": "紧急",
    "dispatch.priority.high": "高",
    "dispatch.priority.medium": "中",
    "dispatch.priority.low": "低",
    "dispatch.action_text": (
        "在 {deadline} 前，从 {source} 调运 {quantity} 辆到 {target}。"
    ),
    "dispatch.reason": (
        "未来 120 分钟预计 {demand:.0f} 笔骑行订单，"
        "当前可借 {available} 辆，目标备车 {target} 辆。"
    ),
    "dashboard.data_mode_label": "虚拟演示数据",
    "dashboard.business_definition": (
        "需求表示每个 30 分钟窗口内预计发生的骑行订单数；"
        "调度建议根据未来 2 小时订单、当前可借车辆和安全库存生成。"
    ),
    "dashboard.consistency.ready": (
        "预测、库存和调度建议使用同一批次数据。"
    ),
    "dashboard.consistency.missing_forecast": (
        "当前没有成功的预测批次。"
    ),
    "dashboard.consistency.missing_inventory": (
        "当前没有可用的库存快照。"
    ),
    "dashboard.consistency.missing_dispatch": (
        "已有预测数据，但尚未生成调度建议。"
    ),
    "dashboard.consistency.stale_dispatch": (
        "调度建议来自较早的预测批次，需要重新生成。"
    ),
    "dashboard.consistency.updating": (
        "已生成新预测，正在刷新调度建议。"
    ),
}

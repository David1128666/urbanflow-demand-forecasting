"""Localized text for forecast-engine command output."""

DISPATCH_REASON_MESSAGES = {
    "en": (
        "Expected ride orders in the next {horizon_minutes} minutes: "
        "{near_term_demand:.0f}. Available bikes: {available_bikes}. "
        "Target stock: {target_bikes}."
    ),
    "zh-CN": (
        "未来 {horizon_minutes} 分钟预计 {near_term_demand:.0f} 笔骑行订单，"
        "当前可借 {available_bikes} 辆，目标备车 {target_bikes} 辆"
    ),
}


def dispatch_reason(language: str, **values: object) -> str:
    selected = language if language in DISPATCH_REASON_MESSAGES else "en"
    return DISPATCH_REASON_MESSAGES[selected].format(**values)

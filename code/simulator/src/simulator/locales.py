"""Localized labels for generated demo data."""

MESSAGES = {
    "en": {
        "city_name": "Virtual City",
        "station_template": "Demo · {scene} {index:03d}",
        "transit": "Transit Hub",
        "business": "Central Business District",
        "residential": "Residential District",
        "mixed": "Mixed Commercial and Residential",
        "leisure": "Leisure District",
    },
    "zh-CN": {
        "city_name": "虚拟城市",
        "station_template": "演示·{scene} {index:03d}",
        "transit": "城市交通枢纽",
        "business": "中央办公区",
        "residential": "大型居住区",
        "mixed": "商业住宅混合区",
        "leisure": "休闲生活区",
    },
}


def message(language: str, key: str, **values: object) -> str:
    selected = language if language in MESSAGES else "en"
    template = MESSAGES[selected][key]
    return template.format(**values)

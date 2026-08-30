def get_localized_text(
    data: dict[str, str] | None,
    locale: str,
    default: str = "",
) -> str:
    if not data:
        return default

    if data.get(locale):
        return data[locale]

    if data.get("en"):
        return data["en"]

    for val in data.values():
        if val:
            return val

    return default

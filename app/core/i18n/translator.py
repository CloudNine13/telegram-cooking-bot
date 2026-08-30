from typing import Any

from app.core.i18n.locales import DEFAULT_LOCALE, TRANSLATIONS


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    locale_dict: dict[str, str] = TRANSLATIONS.get(
        locale,
        TRANSLATIONS.get(DEFAULT_LOCALE, {}),
    )
    template: str = locale_dict.get(
        key,
        TRANSLATIONS.get(DEFAULT_LOCALE, {}).get(key, key),
    )

    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template

    return template

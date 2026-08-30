import asyncio

from deep_translator import GoogleTranslator
from deep_translator.exceptions import BaseError
from requests.exceptions import RequestException


class TranslationService:
    @staticmethod
    def _translate_sync(text: str, target: str, source: str = "auto") -> str:
        try:
            return GoogleTranslator(
                source=source,
                target=target,
            ).translate(text)
        except (
            BaseError,
            RequestException,
            ValueError,
            TypeError,
            RuntimeError,
            TimeoutError,
            ConnectionError,
            OSError,
        ):
            return text

    async def translate_category_name(
        self,
        text: str,
        source: str = "auto",
    ) -> dict[str, str]:
        target_languages: list[str] = ["en", "ru", "es"]
        results: dict[str, str] = {}

        tasks = [
            asyncio.to_thread(self._translate_sync, text, lang, source)
            for lang in target_languages
        ]
        translated_values: list[str] = await asyncio.gather(*tasks)

        for lang, val in zip(target_languages, translated_values, strict=False):
            results[lang] = val or text

        return results

import asyncio
import contextlib
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.schemas.recipe import RecipeDTO


@dataclass(frozen=True, slots=True)
class ExportedPdfResult:
    file_path: Path
    filename: str
    file_size_bytes: int


class PdfExportService:
    def __init__(self, temp_base_dir: Path | None = None) -> None:
        self.temp_base_dir: Path = (
            temp_base_dir
            if temp_base_dir is not None
            else Path(tempfile.gettempdir()) / "cooking_bot_pdf"
        )
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _find_chrome_executable() -> str | None:
        for executable in [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ]:
            path: str | None = shutil.which(executable)
            if path is not None:
                return path

        return None

    @staticmethod
    def _get_output_pdf_size(path: Path) -> int | None:
        if path.exists() and path.is_file():
            size: int = path.stat().st_size
            if size > 0:
                return size

        return None

    async def url_to_pdf(
        self,
        url: str,
        timeout_seconds: int = 60,
    ) -> ExportedPdfResult | None:
        if not url.startswith(("http://", "https://")):
            return None

        chrome_path: str | None = self._find_chrome_executable()
        if chrome_path is None:
            return None

        unique_id: str = uuid.uuid4().hex
        output_pdf: Path = self.temp_base_dir / f"webpage_{unique_id}.pdf"

        cmd = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            f"--print-to-pdf={output_pdf}",
            url,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds,
                )
            except TimeoutError:
                process.kill()
                await process.wait()

                return None

            pdf_size: int | None = await asyncio.to_thread(
                self._get_output_pdf_size,
                output_pdf,
            )

            if process.returncode == 0 and pdf_size is not None:
                return ExportedPdfResult(
                    file_path=output_pdf,
                    filename=output_pdf.name,
                    file_size_bytes=pdf_size,
                )

        except (OSError, ValueError, RuntimeError, asyncio.SubprocessError):
            return None

        return None

    async def recipe_to_pdf(
        self,
        recipe: RecipeDTO,
        locale: str = "en",
        timeout_seconds: int = 30,
    ) -> ExportedPdfResult | None:
        chrome_path: str | None = self._find_chrome_executable()
        if chrome_path is None:
            return None

        unique_id: str = uuid.uuid4().hex
        temp_html_path: Path = self.temp_base_dir / f"recipe_{unique_id}.html"
        output_pdf_path: Path = self.temp_base_dir / f"recipe_{unique_id}.pdf"

        title: str = (
            recipe.title_ru if locale == "ru" and recipe.title_ru else recipe.title_en
        )
        category_name: str = ""
        if recipe.category is not None:
            category_name = (
                recipe.category.name_ru if locale == "ru" else recipe.category.name_en
            )

        instructions: str = (
            recipe.instructions_ru
            if locale == "ru" and recipe.instructions_ru
            else recipe.instructions_en
        )

        ingredients_html_list: list[str] = []
        for ing in recipe.ingredients:
            name: str = ing.name_ru if locale == "ru" and ing.name_ru else ing.name_en
            amount_parts: list[str] = []
            if ing.quantity is not None:
                amount_parts.append(str(ing.quantity))
            if ing.unit is not None:
                amount_parts.append(ing.unit)

            amount_str = f" - {' '.join(amount_parts)}" if amount_parts else ""
            ingredients_html_list.append(f"<li>{name}{amount_str}</li>")

        ingredients_html: str = "".join(ingredients_html_list)
        instructions_formatted: str = instructions.replace("\n", "<br/>")

        ingredients_heading: str = "Ингредиенты" if locale == "ru" else "Ingredients"
        instructions_heading: str = (
            "Инструкция по приготовлению" if locale == "ru" else "Instructions"
        )
        prep_time_label: str = "Время приготовления" if locale == "ru" else "Prep Time"
        category_label: str = "Категория" if locale == "ru" else "Category"
        minutes_unit: str = "мин" if locale == "ru" else "min"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    color: #222;
    line-height: 1.6;
}}
h1 {{
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}}
.meta {{
    font-size: 14px;
    color: #7f8c8d;
    margin-bottom: 20px;
}}
h2 {{
    color: #34495e;
    margin-top: 25px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 5px;
}}
ul {{
    list-style-type: square;
    padding-left: 20px;
}}
li {{
    margin-bottom: 6px;
}}
.instructions {{
    background: #fdfdfd;
    padding: 15px;
    border-left: 4px solid #3498db;
}}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">
<strong>{category_label}:</strong> {category_name} | 
<strong>{prep_time_label}:</strong> {recipe.prep_time_minutes} {minutes_unit}
</div>
<h2>{ingredients_heading}</h2>
<ul>
{ingredients_html}
</ul>
<h2>{instructions_heading}</h2>
<div class="instructions">
{instructions_formatted}
</div>
</body>
</html>
"""

        try:

            def _write_temp_html(path: Path, content: str) -> None:
                path.write_text(content, encoding="utf-8")

            await asyncio.to_thread(_write_temp_html, temp_html_path, html_content)

            cmd = [
                chrome_path,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--print-to-pdf={output_pdf_path}",
                f"file://{temp_html_path}",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds,
                )
            except TimeoutError:
                process.kill()
                await process.wait()

                return None

            pdf_size: int | None = await asyncio.to_thread(
                self._get_output_pdf_size,
                output_pdf_path,
            )

            if process.returncode == 0 and pdf_size is not None:
                return ExportedPdfResult(
                    file_path=output_pdf_path,
                    filename=f"{recipe.id}_{title.replace(' ', '_')}.pdf",
                    file_size_bytes=pdf_size,
                )

        except (OSError, ValueError, RuntimeError, asyncio.SubprocessError):
            return None
        finally:

            def _remove_temp_file(path: Path) -> None:
                with contextlib.suppress(OSError):
                    if path.exists():
                        path.unlink()

            await asyncio.to_thread(_remove_temp_file, temp_html_path)

        return None

    @staticmethod
    async def cleanup(file_path: Path | str) -> None:
        def _do_cleanup() -> None:
            with contextlib.suppress(OSError):
                path = Path(file_path)
                if path.exists() and path.is_file():
                    path.unlink()

        await asyncio.to_thread(_do_cleanup)

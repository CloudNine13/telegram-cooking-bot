import asyncio
import contextlib
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DownloadedMediaResult:
    file_path: Path
    filename: str
    file_size_bytes: int
    title: str | None = None
    duration_seconds: int | None = None


class MediaDownloaderService:
    def __init__(self, temp_base_dir: Path | None = None) -> None:
        self.temp_base_dir: Path = (
            temp_base_dir
            if temp_base_dir is not None
            else Path(tempfile.gettempdir()) / "cooking_bot_media"
        )
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_supported_url(url: str) -> bool:
        lowered: str = url.strip().lower()

        return lowered.startswith(("http://", "https://")) and any(
            domain in lowered
            for domain in [
                "instagram.com",
                "instagr.am",
                "youtube.com",
                "youtu.be",
                "tiktok.com",
                "vimeo.com",
            ]
        )

    async def download_video(
        self,
        url: str,
        timeout_seconds: int = 120,
    ) -> DownloadedMediaResult | None:
        if not self.is_supported_url(url):
            return None

        yt_dlp_path: str | None = shutil.which("yt-dlp")
        unique_id: str = uuid.uuid4().hex
        output_template: str = str(
            self.temp_base_dir / f"{unique_id}_%(id)s.%(ext)s",
        )

        if yt_dlp_path is not None:
            try:
                cmd = [
                    yt_dlp_path,
                    "--no-warnings",
                    "--format",
                    "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format",
                    "mp4",
                    "--max-filesize",
                    "50M",
                    "-o",
                    output_template,
                    url,
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

                if process.returncode != 0:
                    return None

            except (OSError, ValueError, RuntimeError, asyncio.SubprocessError):
                return None
        else:
            try:
                import yt_dlp

                ydl_opts = {
                    "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "outtmpl": output_template,
                    "quiet": True,
                    "no_warnings": True,
                    "max_filesize": 50 * 1024 * 1024,
                }

                def _download() -> None:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                await asyncio.to_thread(_download)
            except (OSError, ValueError, RuntimeError, ImportError):
                return None

        def _find_matching_files() -> list[Path]:
            return list(self.temp_base_dir.glob(f"{unique_id}_*"))

        matching_files: list[Path] = await asyncio.to_thread(
            _find_matching_files,
        )
        if not matching_files:
            return None

        downloaded_file: Path = matching_files[0]

        def _get_file_size(file: Path) -> int:
            return file.stat().st_size

        file_size: int = await asyncio.to_thread(
            _get_file_size,
            downloaded_file,
        )

        return DownloadedMediaResult(
            file_path=downloaded_file,
            filename=downloaded_file.name,
            file_size_bytes=file_size,
            title=None,
            duration_seconds=None,
        )

    @staticmethod
    async def cleanup(file_path: Path | str) -> None:
        def _do_cleanup() -> None:
            with contextlib.suppress(OSError):
                path = Path(file_path)
                if path.exists() and path.is_file():
                    path.unlink()

        await asyncio.to_thread(_do_cleanup)

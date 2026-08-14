import subprocess
import tempfile
from pathlib import Path

from langchain_core.documents import Document

from .base import DocumentLoader, LoaderParsingError
from .pptx_loader import PptxLoader

_CONVERT_TIMEOUT_SECONDS = 60


class PptLegacyLoader(DocumentLoader):
    def load(self, path: str) -> list[Document]:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pptx",
                        "--outdir",
                        tmpdir,
                        path,
                    ],
                    check=True,
                    capture_output=True,
                    timeout=_CONVERT_TIMEOUT_SECONDS,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
                raise LoaderParsingError("ppt", "no se pudo convertir el fichero PPT legacy a PPTX") from exc

            converted = Path(tmpdir) / f"{Path(path).stem}.pptx"
            if not converted.exists():
                raise LoaderParsingError("ppt", "la conversión no generó un fichero PPTX")

            return PptxLoader().load(str(converted))

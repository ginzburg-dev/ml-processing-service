import zipfile
from zipfile import ZipFile
from pathlib import Path
from typing import Any


class ZipArchive:
    def __init__(
        self, out_zip_path: str, compression: Any = zipfile.ZIP_DEFLATED
    ) -> None:
        self.out_zip_path: Path = Path(out_zip_path)
        self.out_zip_path.parent.mkdir(parents=True, exist_ok=True)
        self.compression: Any = compression
        self._zip: ZipFile = zipfile.ZipFile(
            file=self.out_zip_path, mode="w", compression=self.compression
        )

    def add_file(self, filename: str, arcname: str | None = None) -> None:
        arcname = arcname or Path(filename).name
        self._zip.write(filename, arcname)

    def add_bytes(self, arcname: str, data: bytes) -> None:
        self._zip.writestr(arcname, data)

    def close(self) -> Path:
        self._zip.close()
        return self.out_zip_path

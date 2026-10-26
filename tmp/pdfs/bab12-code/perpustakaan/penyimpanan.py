import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .kesalahan import DataRusakError, PenyimpananError


class Penyimpanan(Protocol):
    def muat(self) -> dict: ...
    def simpan(self, data: dict) -> None: ...


class PenyimpananJSON:
    def __init__(self, path):
        self.path = Path(path)

    def muat(self):
        try:
            with self.path.open(encoding="utf-8") as sumber:
                data = json.load(sumber)
        except FileNotFoundError:
            raise  # layanan menentukan perilaku saat belum ada file
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise DataRusakError("File JSON tidak dapat dibaca.") from exc
        except OSError as exc:
            raise PenyimpananError("Gagal membuka file data.") from exc
        if not isinstance(data, dict):
            raise DataRusakError("Isi utama JSON harus berupa object.")
        return data

    def simpan(self, data):
        sementara = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=".perpustakaan-", suffix=".tmp", delete=False,
            ) as tujuan:
                sementara = Path(tujuan.name)
                json.dump(data, tujuan, ensure_ascii=False, indent=2)
            os.replace(sementara, self.path)
        except (OSError, TypeError, ValueError) as exc:
            raise PenyimpananError("Gagal menyimpan data.") from exc
        finally:
            if sementara is not None:
                try:
                    sementara.unlink(missing_ok=True)
                except OSError:
                    pass  # pembersihan tidak menutupi kegagalan utama

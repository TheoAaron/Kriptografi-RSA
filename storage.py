"""Penyimpanan JSON sederhana dengan validasi dan penulisan atomik."""

import json
import os
import tempfile
import threading

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "links.json")
_WRITE_LOCK = threading.RLock()


class StorageError(Exception):
    """Kesalahan yang dapat dijelaskan saat membaca atau menulis storage."""


class Storage:
    def __init__(self, path=DEFAULT_PATH):
        self.path = os.path.abspath(path)
        self.counter = 0
        self.links = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return
        except json.JSONDecodeError as error:
            raise StorageError("File storage bukan JSON yang valid.") from error
        except OSError as error:
            raise StorageError("Storage tidak dapat dibaca.") from error

        if not isinstance(data, dict):
            raise StorageError("Struktur storage harus berupa object JSON.")
        counter = data.get("counter", 0)
        links = data.get("links", {})
        if not isinstance(counter, int) or counter < 0:
            raise StorageError("Nilai counter pada storage tidak valid.")
        if not isinstance(links, dict):
            raise StorageError("Nilai links pada storage tidak valid.")
        for code, entry in links.items():
            if not isinstance(code, str) or not isinstance(entry, dict):
                raise StorageError("Format entry pada storage tidak valid.")
            if not isinstance(entry.get("url"), str) or not isinstance(
                entry.get("signature"), str
            ):
                raise StorageError("Entry storage harus memiliki url dan signature.")
        self.counter = counter
        self.links = links

    def save(self):
        data = {"counter": self.counter, "links": self.links}
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        with _WRITE_LOCK:
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=directory,
                    prefix=".links-",
                    suffix=".tmp",
                    delete=False,
                ) as file:
                    temporary_path = file.name
                    json.dump(data, file, indent=2, ensure_ascii=False)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporary_path, self.path)
            except OSError as error:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)
                raise StorageError("Storage tidak dapat disimpan.") from error

    def next_counter(self):
        current = self.counter
        self.counter += 1
        return current

    def add(self, code, url, signature):
        if code in self.links:
            raise StorageError("Kode pendek sudah digunakan.")
        self.links[code] = {"url": url, "signature": str(signature)}
        try:
            self.save()
        except StorageError:
            del self.links[code]
            raise

    def get(self, code):
        return self.links.get(code)

    def delete(self, code):
        if code not in self.links:
            return False
        entry = self.links.pop(code)
        try:
            self.save()
        except StorageError:
            self.links[code] = entry
            raise
        return True

    def list_all(self):
        return dict(self.links)

"""Service URL shortener dan tanda tangan RSA edukasi."""

import json
import os
from urllib.parse import urlparse

import base62
import hash_edu
import rsa_manual
from storage import Storage, StorageError

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("URL_SHORTENER_DATA_DIR", PROJECT_DIR)
PUBLIC_KEY_FILE = os.path.join(DATA_DIR, "keys_public.json")
PRIVATE_KEY_FILE = os.path.join(DATA_DIR, "keys_private.json")
MAX_URL_LENGTH = 2048


class ShortenerError(Exception):
    """Base error untuk operasi shortener."""


class InvalidUrlError(ShortenerError):
    pass


class KeyError_(ShortenerError):
    pass


class InvalidCodeError(ShortenerError):
    pass


def configure(data_dir=None):
    """Pilih direktori data untuk proses CLI atau dashboard."""
    global DATA_DIR, PUBLIC_KEY_FILE, PRIVATE_KEY_FILE
    configured_dir = data_dir or os.environ.get(
        "URL_SHORTENER_DATA_DIR", PROJECT_DIR
    )
    DATA_DIR = os.path.abspath(configured_dir)
    PUBLIC_KEY_FILE = os.path.join(DATA_DIR, "keys_public.json")
    PRIVATE_KEY_FILE = os.path.join(DATA_DIR, "keys_private.json")


def validate_url(url):
    if not isinstance(url, str):
        raise InvalidUrlError("URL harus berupa teks.")
    url = url.strip()
    parsed = urlparse(url)
    if len(url) > MAX_URL_LENGTH:
        raise InvalidUrlError("URL terlalu panjang (maksimal 2048 karakter).")
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise InvalidUrlError("URL harus memakai http/https dan memiliki hostname.")
    return url


def _load_key(path, private=False):
    try:
        with open(path, "r", encoding="utf-8") as file:
            key = json.load(file)
    except FileNotFoundError as error:
        name = "privat" if private else "publik"
        raise KeyError_(f"Kunci {name} belum ada. Jalankan: python cli.py keygen") from error
    except (json.JSONDecodeError, OSError) as error:
        raise KeyError_("File kunci tidak dapat dibaca.") from error
    required = ("d", "n") if private else ("e", "n")
    if not isinstance(key, dict) or any(
        not isinstance(key.get(item), int) for item in required
    ):
        raise KeyError_("Format file kunci tidak valid.")
    return key


def load_public_key():
    return _load_key(PUBLIC_KEY_FILE)


def load_private_key():
    return _load_key(PRIVATE_KEY_FILE, private=True)


def _validate_code(code):
    try:
        base62.decode(code)
    except (TypeError, ValueError) as error:
        raise InvalidCodeError("Kode pendek tidak valid.") from error


def _digest(url, modulus):
    return hash_edu.hash_to_int(url, modulus)


def shorten(url, storage=None):
    url = validate_url(url)
    storage = storage or Storage(os.path.join(DATA_DIR, "links.json"))
    private_key = load_private_key()
    code = base62.encode(storage.next_counter())
    signature = rsa_manual.sign(_digest(url, private_key["n"]), private_key)
    storage.add(code, url, str(signature))
    return code


def resolve(code, storage=None):
    _validate_code(code)
    storage = storage or Storage(os.path.join(DATA_DIR, "links.json"))
    entry = storage.get(code)
    if entry is None:
        return "not_found", None
    try:
        signature = int(entry["signature"])
    except (KeyError, TypeError, ValueError) as error:
        raise StorageError("Signature pada entry tidak valid.") from error
    public_key = load_public_key()
    digest = _digest(entry["url"], public_key["n"])
    if rsa_manual.verify(signature, digest, public_key):
        return "ok", entry["url"]
    return "tampered", entry["url"]


def list_entries(storage=None):
    storage = storage or Storage(os.path.join(DATA_DIR, "links.json"))
    return storage.list_all()


def delete(code, storage=None):
    _validate_code(code)
    storage = storage or Storage(os.path.join(DATA_DIR, "links.json"))
    return storage.delete(code)

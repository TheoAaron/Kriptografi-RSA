"""Encoding base62 untuk kode pendek URL shortener."""

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)
_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}


def encode(number):
    """Ubah integer >= 0 menjadi string base62."""
    if number < 0:
        raise ValueError("Counter tidak boleh negatif")
    if number == 0:
        return ALPHABET[0]
    digits = []
    while number > 0:
        number, rem = divmod(number, BASE)
        digits.append(ALPHABET[rem])
    return "".join(reversed(digits))


def decode(code):
    """Ubah string base62 menjadi integer."""
    if not code:
        raise ValueError("Kode tidak boleh kosong")
    number = 0
    for ch in code:
        if ch not in _INDEX:
            raise ValueError("Karakter base62 tidak valid: %r" % ch)
        number = number * BASE + _INDEX[ch]
    return number

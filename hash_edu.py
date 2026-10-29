import struct

MASK32 = 0xFFFFFFFF
BLOCK_SIZE = 64


def _left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK32


def _pad(data):
    """Padding mirip Merkle-Damgard: tambah 0x80 lalu panjang pesan (bit)."""
    length_bits = len(data) * 8
    data += b"\x80"
    while len(data) % BLOCK_SIZE != (BLOCK_SIZE - 8):
        data += b"\x00"
    data += struct.pack(">Q", length_bits & 0xFFFFFFFFFFFFFFFF)
    return data


def hash_bytes(data):
    """Kembalikan digest 128-bit sebagai integer."""
    if isinstance(data, str):
        data = data.encode("utf-8")

    h0 = 0x6A09E667
    h1 = 0xBB67AE85
    h2 = 0x3C6EF372
    h3 = 0xA54FF53A

    padded = _pad(data)
    for offset in range(0, len(padded), BLOCK_SIZE):
        block = padded[offset:offset + BLOCK_SIZE]
        w = list(struct.unpack(">16I", block))

        a, b, c, d = h0, h1, h2, h3
        for i in range(16):
            f = (b & c) | (~b & d & MASK32)
            g = _left_rotate(a, 5) + f + w[i] + (0x5A827999 + i)
            a, d, c, b = d, c, b, (g & MASK32)

        h0 = (h0 + a) & MASK32
        h1 = (h1 + b) & MASK32
        h2 = (h2 + c) & MASK32
        h3 = (h3 + d) & MASK32

    return (h0 << 96) | (h1 << 64) | (h2 << 32) | h3


def hash_to_int(text, modulus=None):
    """Hash teks, opsional dikurangi modulo agar muat di bawah modulus RSA."""
    digest = hash_bytes(text)
    if modulus is not None:
        digest %= modulus
    return digest

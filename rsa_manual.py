"""Implementasi RSA manual (tanpa library kriptografi eksternal).

Hanya memakai modul standar Python: random, json.
Semua operasi matematis (prima, gcd, invers modulo, modexp, sign/verify)
ditulis sendiri untuk keperluan tugas edukasi.
"""

import random


def gcd(a, b):
    """Greatest common divisor via algoritma Euclid."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def extended_gcd(a, b):
    """Kembalikan (g, x, y) sehingga a*x + b*y = g = gcd(a, b)."""
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def mod_inverse(a, m):
    """Invers modulo dari a terhadap m (a^-1 mod m)."""
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError("Invers modulo tidak ada (gcd != 1)")
    return x % m


def power_mod(base, exp, mod):
    """Fast modular exponentiation (square-and-multiply) manual.

    Menghitung base**exp mod mod tanpa memakai pow() bawaan.
    """
    result = 1
    base = base % mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result


def is_probable_prime(n, rounds=40):
    """Uji prima Miller-Rabin. Mengembalikan True jika n kemungkinan prima."""
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1

    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = power_mod(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits):
    """Bangkitkan bilangan prima acak dengan jumlah bit tertentu."""
    while True:
        candidate = random.getrandbits(bits)
        candidate |= (1 << (bits - 1)) | 1
        if is_probable_prime(candidate):
            return candidate


def generate_keypair(bits=512, e=65537):
    """Bangkitkan pasangan kunci RSA.

    bits : ukuran tiap prima (bit). Modulus n akan berukuran ~2*bits bit.
    e    : eksponen publik (harus koprima dengan phi).
    Return: (public_key, private_key) sebagai dict {e/n} dan {d/n}.
    """
    half = bits // 2 if bits > 64 else bits
    while True:
        p = generate_prime(half)
        q = generate_prime(half)
        if p == q:
            continue
        n = p * q
        phi = (p - 1) * (q - 1)
        if gcd(e, phi) != 1:
            continue
        d = mod_inverse(e, phi)
        public_key = {"e": e, "n": n}
        private_key = {"d": d, "n": n}
        return public_key, private_key


def sign(message_int, private_key):
    """Tanda tangani sebuah integer dengan kunci privat: sig = m^d mod n."""
    n = private_key["n"]
    d = private_key["d"]
    if message_int >= n:
        raise ValueError("Pesan lebih besar dari modulus n")
    return power_mod(message_int, d, n)


def verify(signature_int, message_int, public_key):
    """Verifikasi tanda tangan: cek sig^e mod n == message_int."""
    n = public_key["n"]
    e = public_key["e"]
    if message_int >= n:
        raise ValueError("Pesan lebih besar dari modulus n")
    return power_mod(signature_int, e, n) == message_int

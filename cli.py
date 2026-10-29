"""Entrypoint CLI URL shortener dengan RSA manual untuk edukasi."""

import argparse
import json
import os
import sys

import rsa_manual
import shortener
from storage import StorageError


def cmd_keygen(args):
    shortener.configure(args.data_dir)
    public_key, private_key = rsa_manual.generate_keypair(bits=args.bits)
    os.makedirs(shortener.DATA_DIR, exist_ok=True)
    with open(shortener.PUBLIC_KEY_FILE, "w", encoding="utf-8") as file:
        json.dump(public_key, file, indent=2)
    with open(shortener.PRIVATE_KEY_FILE, "w", encoding="utf-8") as file:
        json.dump(private_key, file, indent=2)
    print("Kunci berhasil dibuat di", shortener.DATA_DIR)
    print("  publik:", shortener.PUBLIC_KEY_FILE)


def cmd_shorten(args):
    print("URL asli   :", args.url)
    print("Kode pendek:", shortener.shorten(args.url))


def cmd_resolve(args):
    status, url = shortener.resolve(args.code)
    if status == "ok":
        print("[OK] Tanda tangan valid.\nURL asli:", url)
    elif status == "tampered":
        print("[GAGAL] Verifikasi tanda tangan gagal.\nURL tersimpan:", url)
        return 1
    else:
        print("[ERROR] Kode tidak ditemukan:", args.code)
        return 1
    return 0


def cmd_list(args):
    entries = shortener.list_entries()
    if not entries:
        print("(kosong)")
        return 0
    print("%-8s %-50s %s" % ("KODE", "URL", "SIGNATURE"))
    for code, data in entries.items():
        signature = data["signature"]
        sig_short = signature if len(signature) <= 20 else signature[:17] + "..."
        url = data["url"]
        url_short = url if len(url) <= 50 else url[:47] + "..."
        print("%-8s %-50s %s" % (code, url_short, sig_short))
    return 0


def cmd_delete(args):
    if shortener.delete(args.code):
        print("Kode dihapus:", args.code)
        return 0
    print("Kode tidak ditemukan:", args.code)
    return 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cli.py", description="URL Shortener RSA manual (educational mode)."
    )
    parser.add_argument("--data-dir", help="Direktori data key dan links.json")
    sub = parser.add_subparsers(dest="command", required=True)
    keygen = sub.add_parser("keygen", help="Bangkitkan pasangan kunci RSA")
    keygen.add_argument("--bits", type=int, default=512)
    keygen.set_defaults(func=cmd_keygen)
    shorten = sub.add_parser("shorten", help="Pendekkan URL")
    shorten.add_argument("url")
    shorten.set_defaults(func=cmd_shorten)
    resolve = sub.add_parser("resolve", help="Verifikasi URL")
    resolve.add_argument("code")
    resolve.set_defaults(func=cmd_resolve)
    listing = sub.add_parser("list", help="Tampilkan semua entry")
    listing.set_defaults(func=cmd_list)
    deleting = sub.add_parser("delete", help="Hapus entry")
    deleting.add_argument("code")
    deleting.set_defaults(func=cmd_delete)
    return parser


def main():
    args = build_parser().parse_args()
    shortener.configure(args.data_dir)
    try:
        return args.func(args) or 0
    except (shortener.ShortenerError, StorageError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# URL Shortener RSA (Educational Mode)

Contoh sederhana URL shortener lokal dengan Base62 dan tanda tangan RSA
manual. Tujuannya untuk mempelajari alur hash, tanda tangan, dan verifikasi;
**bukan** implementasi keamanan produksi. Hash buatan sendiri, textbook RSA,
dan pembangkitan prima dengan `random` tidak boleh dipakai untuk melindungi
data nyata.

## Instalasi dan data

Python 3.10+ diperlukan. Dashboard memakai Flask:

```bash
python -m pip install -r requirements.txt
```

Secara default key dan `links.json` berada di folder proyek. Gunakan
`--data-dir` atau environment variable `URL_SHORTENER_DATA_DIR` untuk
memisahkan data runtime:

```bash
python cli.py --data-dir .url_shortener_data keygen --bits 512
```

Jangan membagikan `keys_private.json`. File key dan data runtime sudah
dimasukkan ke `.gitignore`. Untuk menjaga folder proyek tetap rapi, gunakan
`.url_shortener_data` sebagai direktori data lokal.

## Struktur proyek

| Lokasi | Fungsi |
|---|---|
| `app.py` dan `templates/` | Dashboard lokal berbasis Flask |
| `cli.py` | Antarmuka command line |
| `shortener.py` | Layanan shorten, resolve, list, dan delete |
| `rsa_manual.py`, `hash_edu.py`, `base62.py` | Komponen kriptografi edukasi dan encoding |
| `storage.py` | Penyimpanan JSON dengan validasi dan penulisan atomik |
| `tests/` | Pengujian unit dan integrasi |
| `build_report.py` | Generator laporan DOCX |
| `.url_shortener_data/` | Data runtime lokal; tidak untuk dibagikan |

## CLI

```bash
python cli.py keygen
python cli.py shorten "https://example.com/halaman"
python cli.py resolve 0
python cli.py list
python cli.py delete 0
```

URL harus memakai `http` atau `https` dan memiliki hostname. Kegagalan key,
storage, URL, atau kode ditampilkan sebagai pesan singkat dengan exit code
non-zero.

## Dashboard lokal

```bash
python -m flask --app app:create_app run --debug
```

Buka `http://127.0.0.1:5000`. Dashboard hanya lokal, tidak memiliki login dan
tidak mengklaim keamanan multi-user. Resolve selalu memverifikasi signature
lebih dulu dan tidak melakukan redirect otomatis. Endpoint `/health` hanya
menampilkan status storage/key, tidak pernah mengirim private key atau
signature.

## Pengujian

```bash
python -m unittest discover -s tests -v
```

Test memakai temporary directory sehingga tidak mengubah key atau `links.json`
contoh.

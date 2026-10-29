"""Dashboard lokal Flask yang memakai service shortener yang sama dengan CLI."""

import os

from flask import Flask, flash, redirect, render_template, request, url_for

import shortener
from storage import Storage, StorageError


def create_app(data_dir=None):
    shortener.configure(data_dir)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "URL_SHORTENER_FLASK_SECRET", "local-development-only"
    )

    def storage():
        return Storage(os.path.join(shortener.DATA_DIR, "links.json"))

    @app.get("/")
    def index():
        try:
            entries = shortener.list_entries(storage())
            key_ready = os.path.exists(shortener.PUBLIC_KEY_FILE)
            status = "Ready" if key_ready else "Key missing"
        except (StorageError, OSError) as error:
            entries = {}
            status = "Storage error"
            flash(str(error), "error")
        return render_template("index.html", entries=entries, status=status)

    @app.post("/shorten")
    def shorten_url():
        try:
            code = shortener.shorten(request.form.get("url", ""), storage())
            flash(f"URL berhasil dipendekkan menjadi {code}.", "success")
        except (shortener.ShortenerError, StorageError, OSError) as error:
            flash(str(error), "error")
        return redirect(url_for("index"))

    @app.get("/resolve/<code>")
    def resolve_url(code):
        try:
            status, url = shortener.resolve(code, storage())
        except (shortener.ShortenerError, StorageError, OSError) as error:
            flash(str(error), "error")
            return redirect(url_for("index"))
        if status == "ok":
            flash(f"Verified: {url}", "success")
        elif status == "tampered":
            flash("Tampered: tanda tangan tidak valid; redirect tidak dilakukan.", "error")
        else:
            flash("Not found: kode tidak ditemukan.", "error")
        return redirect(url_for("index"))

    @app.post("/delete/<code>")
    def delete_url(code):
        try:
            if shortener.delete(code, storage()):
                flash("Link dihapus.", "success")
            else:
                flash("Not found: kode tidak ditemukan.", "error")
        except (shortener.ShortenerError, StorageError, OSError) as error:
            flash(str(error), "error")
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        try:
            shortener.list_entries(storage())
            storage_status = "ok"
        except StorageError:
            storage_status = "error"
        return {
            "status": "ok" if storage_status == "ok" else "error",
            "storage": storage_status,
            "key": "ok" if os.path.exists(shortener.PUBLIC_KEY_FILE) else "missing",
            "educational_mode": True,
        }, (200 if storage_status == "ok" else 503)

    return app


if __name__ == "__main__":
    create_app().run(debug=False)

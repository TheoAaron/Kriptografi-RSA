import json
import os
import tempfile
import unittest

import base62
import hash_edu
import rsa_manual
import shortener
from storage import Storage, StorageError


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        shortener.configure(self.directory.name)
        public, private = rsa_manual.generate_keypair(bits=128)
        with open(shortener.PUBLIC_KEY_FILE, "w", encoding="utf-8") as file:
            json.dump(public, file)
        with open(shortener.PRIVATE_KEY_FILE, "w", encoding="utf-8") as file:
            json.dump(private, file)
        self.storage = Storage(os.path.join(self.directory.name, "links.json"))

    def tearDown(self):
        self.directory.cleanup()

    def test_base62_and_hash(self):
        self.assertEqual(base62.decode(base62.encode(12345)), 12345)
        self.assertEqual(hash_edu.hash_bytes("abc"), hash_edu.hash_bytes("abc"))
        with self.assertRaises(ValueError):
            base62.decode("!")

    def test_shorten_resolve_tampered_delete(self):
        code = shortener.shorten("https://example.com/a", self.storage)
        status, url = shortener.resolve(code, self.storage)
        self.assertEqual((status, url), ("ok", "https://example.com/a"))
        self.storage.links[code]["url"] = "https://example.com/changed"
        self.assertEqual(shortener.resolve(code, self.storage)[0], "tampered")
        self.storage.links[code]["url"] = "https://example.com/a"
        self.assertTrue(shortener.delete(code, self.storage))
        self.assertEqual(shortener.resolve(code, self.storage)[0], "not_found")

    def test_invalid_url_and_corrupt_json(self):
        with self.assertRaises(shortener.InvalidUrlError):
            shortener.shorten("ftp://example.com", self.storage)
        path = os.path.join(self.directory.name, "broken.json")
        with open(path, "w", encoding="utf-8") as file:
            file.write("{broken")
        with self.assertRaises(StorageError):
            Storage(path)

    def test_missing_key(self):
        os.remove(shortener.PRIVATE_KEY_FILE)
        with self.assertRaises(shortener.KeyError_):
            shortener.shorten("https://example.com", self.storage)

    def test_rsa_sign_verify(self):
        public, private = rsa_manual.generate_keypair(bits=128)
        signature = rsa_manual.sign(42, private)
        self.assertTrue(rsa_manual.verify(signature, 42, public))
        self.assertFalse(rsa_manual.verify(signature, 43, public))


@unittest.skipUnless(__import__("importlib").util.find_spec("flask"), "Flask belum terpasang")
class DashboardTests(unittest.TestCase):
    def test_dashboard_routes(self):
        from app import create_app
        with tempfile.TemporaryDirectory() as directory:
            shortener.configure(directory)
            public, private = rsa_manual.generate_keypair(bits=128)
            for path, data in (
                (shortener.PUBLIC_KEY_FILE, public),
                (shortener.PRIVATE_KEY_FILE, private),
            ):
                with open(path, "w", encoding="utf-8") as file:
                    json.dump(data, file)
            client = create_app(directory).test_client()
            self.assertEqual(client.get("/health").status_code, 200)
            response = client.post("/shorten", data={"url": "https://example.com"})
            self.assertEqual(response.status_code, 302)
            self.assertNotIn("private", client.get("/").get_data(as_text=True).lower())


if __name__ == "__main__":
    unittest.main()

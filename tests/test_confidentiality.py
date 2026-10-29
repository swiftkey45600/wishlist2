"""Private records and photos must not leak through errors or numeric IDs."""
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET_KEY", "confidentiality-tests")
from fastapi.testclient import TestClient
from PIL import Image
from app.database import get_connection, init_db
from app.main import app
from app.utils.security import verify_password


class ConfidentialityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.enterContext(patch("app.database.DATABASE_PATH", root / "db"))
        self.enterContext(patch("app.routers.image_router.UPLOAD_DIR", root))
        init_db()
        self.client = self.enterContext(TestClient(app))
        self.password = "SecretPass123"
        def register(login):
            response = self.client.post("/auth/register", json={"name": login, "login": login, "password": self.password})
            self.assertEqual(response.status_code, 200, response.text)
            return {"Authorization": "Bearer " + response.json()["access_token"]}
        self.owner, self.other = register("owner"), register("other")
        image = io.BytesIO()
        Image.new("RGB", (4, 4), "red").save(image, format="PNG")
        self.image_bytes = image.getvalue()

    def upload(self, headers):
        response = self.client.post("/images", headers=headers, files={"file": ("gift.png", self.image_bytes, "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_password_is_hashed_salted_and_never_echoed(self):
        with get_connection() as conn:
            hashes = [row["password_hash"] for row in conn.execute("SELECT password_hash FROM users WHERE login IN ('owner','other')")]
        self.assertNotEqual(hashes[0], hashes[1])
        for stored in hashes:
            self.assertNotEqual(stored, self.password)
            self.assertTrue(verify_password(self.password, stored))
        invalid = self.client.post("/auth/register", json={"name": "Test", "login": "new", "password": {"password": self.password}})
        self.assertEqual(invalid.status_code, 422)
        self.assertNotIn(self.password, invalid.text)
        for login in ("owner", "missing"):
            response = self.client.post("/auth/login", json={"login": login, "password": "wrong"})
            self.assertEqual(response.json()["detail"], "Invalid login or password")
        profile = self.client.get("/users/me", headers=self.owner)
        self.assertNotIn("password", profile.text)
        self.assertIn("no-store", profile.headers["cache-control"])

    def test_image_requires_owner_or_an_explicit_capability(self):
        image = self.upload(self.owner)
        path = f"/images/{image['id']}"
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get(path, headers=self.other).status_code, 404)
        self.assertEqual(self.client.get(path, headers=self.owner).status_code, 200)
        self.assertEqual(self.client.get(image["image_url"]).content, self.image_bytes)
        self.assertEqual(self.client.get(path + "?key=" + "0" * 64).status_code, 404)
        for endpoint, body in (("/wishes/", {"title": "Stolen", "image_id": image["id"]}),
                               ("/events/", {"title": "Stolen", "cover_image_id": image["id"]})):
            self.assertEqual(self.client.post(endpoint, headers=self.other, json=body).status_code, 404)
        # Independent uploads of identical bytes are legitimate and still deduplicate.
        duplicate = self.upload(self.other)
        self.assertEqual(duplicate["id"], image["id"])
        self.assertEqual(self.client.post("/wishes/", headers=self.other, json={"title": "Own photo", "image_id": image["id"]}).status_code, 201)

    def test_share_exposes_selected_items_only_and_can_be_revoked(self):
        image = self.upload(self.owner)
        selected = self.client.post("/wishes/", headers=self.owner, json={"title": "Selected", "image_id": image["id"]}).json()
        self.client.post("/wishes/", headers=self.owner, json={"title": "Never shared"})
        token = self.client.post("/wish-shares/", headers=self.owner, json={"items": [{"kind": "wish", "id": selected["id"]}]}).json()["token"]
        url = f"/wish-shares/{token}"
        result = self.client.get(url)
        self.assertNotIn("Never shared", result.text)
        self.assertEqual(result.json()["items"][0]["status"], "available")
        self.assertEqual(self.client.get(result.json()["items"][0]["image_url"]).status_code, 200)
        self.assertEqual(self.client.delete(url, headers=self.other).status_code, 404)
        self.assertEqual(self.client.delete(url, headers=self.owner).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url + "/items/0/reservation", json={"name": "Guest", "secret_word": "winter"}).status_code, 404)

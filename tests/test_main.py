import unittest

from main import Cafe, create_app, db


class CafeApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "CAFE_API_KEY": "test-key",
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def add_cafe(self, **overrides):
        values = {
            "name": "Test Cafe",
            "map_url": "https://maps.example/cafe",
            "img_url": "https://images.example/cafe.jpg",
            "loc": "London",
            "seats": "20",
            "wifi": "on",
        }
        values.update(overrides)
        return self.client.post("/add", data=values)

    def test_random_returns_not_found_when_no_cafes_exist(self):
        response = self.client.get("/random")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"]["message"], "No cafes are available.")

    def test_search_requires_a_location(self):
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 400)

    def test_add_validates_required_fields(self):
        response = self.client.post("/add", data={"name": "Incomplete Cafe"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("map_url", response.json["error"]["message"])

    def test_add_parses_false_boolean_values_and_returns_created(self):
        response = self.add_cafe(wifi="false", sockets="off", toilet="0", calls="no")

        self.assertEqual(response.status_code, 201)
        with self.app.app_context():
            cafe = db.session.execute(
                db.select(Cafe).where(Cafe.name == "Test Cafe")
            ).scalar_one()
            self.assertFalse(cafe.has_wifi)
            self.assertFalse(cafe.has_sockets)
            self.assertFalse(cafe.has_toilet)
            self.assertFalse(cafe.can_take_calls)

    def test_add_rejects_duplicate_names(self):
        self.add_cafe()

        response = self.add_cafe()

        self.assertEqual(response.status_code, 409)

    def test_add_rejects_invalid_boolean_values(self):
        response = self.add_cafe(wifi="sometimes")

        self.assertEqual(response.status_code, 400)

    def test_update_price_requires_a_price_and_existing_cafe(self):
        self.assertEqual(self.client.patch("/update-price/1").status_code, 400)
        self.assertEqual(
            self.client.patch("/update-price/1?new_price=3.50").status_code, 404
        )

    def test_update_price_updates_existing_cafe(self):
        self.add_cafe()

        response = self.client.patch("/update-price/1?new_price=3.50")

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            cafe = db.session.get(Cafe, 1)
            self.assertEqual(cafe.coffee_price, "3.50")

    def test_delete_requires_configured_header_key(self):
        self.add_cafe()

        response = self.client.delete(
            "/report-closed/1", query_string={"api-key": "test-key"}
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_reports_missing_server_configuration(self):
        self.app.config["CAFE_API_KEY"] = None

        response = self.client.delete("/report-closed/1")

        self.assertEqual(response.status_code, 503)

    def test_delete_succeeds_with_configured_header_key(self):
        self.add_cafe()

        response = self.client.delete(
            "/report-closed/1", headers={"X-API-Key": "test-key"}
        )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()

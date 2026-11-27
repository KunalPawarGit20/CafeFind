# Cafe & WiFi API

A small Flask cafe finder and JSON API for discovering and sharing cafes with Wi-Fi, seating, and other amenities.

## Requirements

- Python 3.10 or newer

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:CAFE_API_KEY = "choose-a-local-secret"
python main.py
```

The app is available at <http://127.0.0.1:5000>. Debug mode is off by default. To enable it for local development only, set `FLASK_DEBUG=1`.

The SQLite database is created at `instance/cafes.db` automatically and starts empty. Add cafes with `POST /add`. Set `DATABASE_URL` to use another SQLAlchemy database URL.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Show the API landing page |
| `GET` | `/all` | List cafes alphabetically |
| `GET` | `/random` | Get a random cafe |
| `GET` | `/search?loc=LOCATION` | Find cafes at an exact location |
| `POST` | `/add` | Add a cafe using form-encoded fields |
| `PATCH` | `/update-price/<cafe_id>?new_price=PRICE` | Update a cafe's coffee price |
| `DELETE` | `/report-closed/<cafe_id>` | Delete a cafe; requires the `X-API-Key` header |

The add endpoint accepts `name`, `map_url`, `img_url`, `loc`, and `seats`. Optional fields are `coffee_price`, `toilet`, `wifi`, `sockets`, and `calls`. Boolean fields accept values such as `true`, `false`, `on`, or `off`; omitted checkboxes are treated as false.

Example requests:

```sh
curl "http://127.0.0.1:5000/all"
curl "http://127.0.0.1:5000/search?loc=London"
curl -X POST http://127.0.0.1:5000/add \
  -d "name=Example Cafe" \
  -d "map_url=https://maps.example/cafe" \
  -d "img_url=https://images.example/cafe.jpg" \
  -d "loc=London" \
  -d "seats=20" \
  -d "wifi=true"
curl -X DELETE http://127.0.0.1:5000/report-closed/1 \
  -H "X-API-Key: choose-a-local-secret"
```

Set `CAFE_API_KEY` before starting the app to enable the delete endpoint. Keep this value private and do not commit it.

## Tests

Run the test suite with Python's built-in test runner:

```powershell
python -m unittest discover -s tests
```

## License

No license is included. Choose and add a license before allowing others to reuse or distribute this project.

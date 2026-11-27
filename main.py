import hmac
import os
import random

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str | None] = mapped_column(String(250), nullable=True)

    def to_dict(self) -> dict[str, int | str | bool | None]:
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


def _error(message: str, status: int):
    return jsonify(error={"message": message}), status


def _form_value(field: str) -> str | None:
    value = request.form.get(field)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _form_boolean(field: str) -> bool:
    value = request.form.get(field)
    if value is None:
        return False

    normalized = value.strip().lower()
    if normalized in {"1", "true", "on", "yes"}:
        return True
    if normalized in {"", "0", "false", "off", "no"}:
        return False
    raise ValueError(f"{field} must be a boolean value.")


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///cafes.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CAFE_API_KEY=os.environ.get("CAFE_API_KEY"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/random")
    def get_random_cafe():
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        if not cafes:
            return _error("No cafes are available.", 404)
        return jsonify(cafe=random.choice(cafes).to_dict())

    @app.route("/all")
    def get_all_cafes():
        cafes = db.session.execute(db.select(Cafe).order_by(Cafe.name)).scalars().all()
        return jsonify(cafes=[cafe.to_dict() for cafe in cafes])

    @app.route("/search")
    def search():
        location = request.args.get("loc", "").strip()
        if not location:
            return _error("The 'loc' query parameter is required.", 400)

        cafes = (
            db.session.execute(db.select(Cafe).where(Cafe.location == location))
            .scalars()
            .all()
        )
        if not cafes:
            return _error("Sorry, we don't have a cafe at that location.", 404)
        return jsonify(cafes=[cafe.to_dict() for cafe in cafes])

    @app.route("/add", methods=["POST"])
    def post_new_cafe():
        required_fields = ("name", "map_url", "img_url", "loc", "seats")
        values = {field: _form_value(field) or "" for field in required_fields}
        missing_fields = [
            field for field, value in values.items() if not value
        ]
        if missing_fields:
            return _error(
                f"Required fields are missing or empty: {', '.join(missing_fields)}.",
                400,
            )

        try:
            new_cafe = Cafe(
                name=values["name"],
                map_url=values["map_url"],
                img_url=values["img_url"],
                location=values["loc"],
                seats=values["seats"],
                has_sockets=_form_boolean("sockets"),
                has_toilet=_form_boolean("toilet"),
                has_wifi=_form_boolean("wifi"),
                can_take_calls=_form_boolean("calls"),
                coffee_price=_form_value("coffee_price"),
            )
        except ValueError as exc:
            return _error(str(exc), 400)

        db.session.add(new_cafe)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return _error("A cafe with that name already exists.", 409)
        return jsonify(response={"success": "Successfully added the new cafe."}), 201

    @app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
    def patch_new_price(cafe_id: int):
        new_price = request.args.get("new_price", "").strip()
        if not new_price:
            return _error("The 'new_price' query parameter is required.", 400)

        cafe = db.session.get(Cafe, cafe_id)
        if cafe is None:
            return _error("A cafe with that id was not found.", 404)

        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."})

    @app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
    def delete_cafe(cafe_id: int):
        expected_key = app.config.get("CAFE_API_KEY")
        supplied_key = request.headers.get("X-API-Key")
        if not expected_key:
            return _error("Cafe deletion is not configured on this server.", 503)
        if not supplied_key or not hmac.compare_digest(
            supplied_key.encode("utf-8"), expected_key.encode("utf-8")
        ):
            return _error("A valid X-API-Key header is required.", 403)

        cafe = db.session.get(Cafe, cafe_id)
        if cafe is None:
            return _error("A cafe with that id was not found.", 404)

        db.session.delete(cafe)
        db.session.commit()
        return jsonify(response={"success": "Successfully deleted the cafe."})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

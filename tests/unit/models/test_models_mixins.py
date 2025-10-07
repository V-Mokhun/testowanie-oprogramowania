import types
import sqlalchemy as sa
from app.models import PaginatedAPIMixin, User


def test_paginated_api_mixin_to_collection_dict(app, monkeypatch):
    class Item:
        def __init__(self, i):
            self.i = i

        def to_dict(self):
            return {"i": self.i}

    resources = types.SimpleNamespace(
        items=[Item(1), Item(2)],
        pages=5,
        total=42,
        has_next=True,
        has_prev=True,
        next_num=2,
        prev_num=1,
    )

    from app import db

    monkeypatch.setattr(
        db, "paginate", lambda q, page, per_page, error_out=False: resources
    )

    with app.test_request_context("/?page=1"):
        data = PaginatedAPIMixin.to_collection_dict(
            sa.select(User), page=1, per_page=10, endpoint="api.get_users"
        )

    assert data["_meta"]["page"] == 1
    assert data["_meta"]["per_page"] == 10
    assert data["_meta"]["total_pages"] == 5
    assert data["_meta"]["total_items"] == 42
    assert data["items"] == [{"i": 1}, {"i": 2}]
    assert (
        "self" in data["_links"]
        and "next" in data["_links"]
        and "prev" in data["_links"]
    )

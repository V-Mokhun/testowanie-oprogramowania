import json


def _auth_ok(monkeypatch):
    from app.api import auth as auth_mod

    auth_mod.token_auth.verify_token_callback = lambda t: object()


def test_create_user_success_and_duplicates(client, monkeypatch):
    from app import db

    side = iter([None, None, 0, 0, 0])
    db.session.scalar.side_effect = lambda *a, **k: next(side)
    db.session.commit.return_value = None

    captured = {}

    def _add(obj):
        captured["user"] = obj
        import datetime as _dt

        obj.id = 10
        if not getattr(obj, "last_seen", None):
            obj.last_seen = _dt.datetime.now(_dt.timezone.utc)

    db.session.add.side_effect = _add

    payload = {"username": "u1", "email": "u1@example.com", "password": "P@ssw0rd"}
    r = client.post(
        "/api/users", data=json.dumps(payload), content_type="application/json"
    )
    assert r.status_code == 201
    assert r.get_json()["username"] == "u1"

    # Duplicate username
    db.session.scalar.side_effect = [object()]
    r2 = client.post(
        "/api/users", data=json.dumps(payload), content_type="application/json"
    )
    assert r2.status_code == 400


def test_get_user_requires_auth_and_works_when_authorized(client, monkeypatch):
    r = client.get("/api/users/1")
    assert r.status_code in (401, 403)

    _auth_ok(monkeypatch)
    from app import db

    class U:
        def to_dict(self):
            return {"id": 1, "username": "u"}

    db.get_or_404 = lambda Model, ident: U()
    r2 = client.get("/api/users/1", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200 and r2.get_json()["username"] == "u"


def test_list_users_pagination_shape(client, monkeypatch):
    _auth_ok(monkeypatch)

    from app import db

    class Item:
        def __init__(self, i):
            self.i = i

        def to_dict(self):
            return {"i": self.i}

    class Resources:
        items = [Item(1), Item(2)]
        pages = 3
        total = 20
        has_next = True
        has_prev = False
        next_num = 2
        prev_num = None

    db.paginate = lambda q, page, per_page, error_out=False: Resources

    r = client.get(
        "/api/users?page=1&per_page=2", headers={"Authorization": "Bearer t"}
    )
    j = r.get_json()
    assert r.status_code == 200
    assert j["_meta"]["page"] == 1
    assert j["_meta"]["total_items"] == 20
    assert j["items"] == [{"i": 1}, {"i": 2}]


def test_followers_and_following_endpoints(client, monkeypatch):
    _auth_ok(monkeypatch)
    from app import db

    class U:
        def __init__(self):
            class Rel:
                def select(self):
                    return "query"

            self.followers = Rel()
            self.following = Rel()

    db.get_or_404 = lambda Model, ident: U()

    class Resources:
        items = []
        pages = 1
        total = 0
        has_next = False
        has_prev = False
        next_num = None
        prev_num = None

    db.paginate = lambda q, page, per_page, error_out=False: Resources

    r1 = client.get("/api/users/1/followers", headers={"Authorization": "Bearer t"})
    r2 = client.get("/api/users/1/following", headers={"Authorization": "Bearer t"})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.get_json()["items"] == [] and r2.get_json()["items"] == []


def test_user_update_owner_check_and_duplicates(client, monkeypatch):
    _auth_ok(monkeypatch)
    from app.api import auth as auth_mod
    from app import db

    class Owner:
        id = 1

    auth_mod.token_auth.current_user = lambda: Owner()

    class U:
        username = "old"
        email = "old@example.com"

        def from_dict(self, data, new_user=False):
            self.username = data.get("username", self.username)
            self.email = data.get("email", self.email)

        def to_dict(self):
            return {"id": 1, "username": self.username, "email": self.email}

    db.get_or_404 = lambda Model, ident: U()

    # Duplicate username
    db.session.scalar.side_effect = [object()]
    r_dup = client.put(
        "/api/users/1",
        data=json.dumps({"username": "new"}),
        content_type="application/json",
        headers={"Authorization": "Bearer t"},
    )
    assert r_dup.status_code == 400

    db.session.scalar.side_effect = [None, None]
    r_ok = client.put(
        "/api/users/1",
        data=json.dumps({"username": "new", "email": "n@example.com"}),
        content_type="application/json",
        headers={"Authorization": "Bearer t"},
    )
    assert r_ok.status_code == 200 and r_ok.get_json()["username"] == "new"

    auth_mod.token_auth.current_user = lambda: type("X", (), {"id": 2})()
    r_403 = client.put(
        "/api/users/1",
        data=json.dumps({"username": "new", "email": "n@example.com"}),
        content_type="application/json",
        headers={"Authorization": "Bearer t"},
    )
    assert r_403.status_code == 403

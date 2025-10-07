def test_login_redirect_when_authenticated(client, monkeypatch):
    class CU:
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    r = client.get("/auth/login")
    assert r.status_code in (302, 303)


def test_login_invalid_and_valid(client, monkeypatch):
    from app import db

    db.session.scalar.return_value = None
    r = client.post(
        "/auth/login", data={"username": "u", "password": "p"}, follow_redirects=False
    )
    assert r.status_code in (302, 303)

    class U:
        def __init__(self):
            self.username = "u"
            self.is_active = True

        def check_password(self, p):
            return True

        def get_id(self):
            return "1"

    db.session.scalar.return_value = U()
    r2 = client.post(
        "/auth/login?next=/index",
        data={"username": "u", "password": "p", "remember_me": "y"},
        follow_redirects=False,
    )
    assert r2.status_code in (302, 303)


def test_logout_redirects(client, monkeypatch):
    class CU:
        is_authenticated = False

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    r = client.get("/auth/logout")
    assert r.status_code in (302, 303)


def test_register_redirect_when_authenticated(client, monkeypatch):
    class CU:
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    r = client.get("/auth/register")
    assert r.status_code in (302, 303)


def test_register_success(client, monkeypatch):
    from app import db

    db.session.commit.return_value = None

    class CU:
        is_authenticated = False

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    r = client.post(
        "/auth/register",
        data={
            "username": "u",
            "email": "e@example.com",
            "password": "p",
            "password2": "p",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)


def test_reset_password_request_flow(client, monkeypatch):
    class CU:
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    r = client.get("/auth/reset_password_request")
    assert r.status_code in (302, 303)

    class CU2:
        is_authenticated = False

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU2())
    from app import db

    class U:
        email = "e@example.com"

        def get_reset_password_token(self):
            return "token"

    db.session.scalar.return_value = U()
    called = {"n": 0}

    def _send(u):
        called["n"] += 1

    monkeypatch.setattr("app.auth.routes.send_password_reset_email", _send)
    r2 = client.post(
        "/auth/reset_password_request",
        data={"email": "e@example.com"},
        follow_redirects=False,
    )
    assert r2.status_code in (302, 303)
    assert called["n"] == 1


def test_reset_password_with_token(client, monkeypatch):
    class CU:
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    r = client.get("/auth/reset_password/abc")
    assert r.status_code in (302, 303)

    class CU2:
        is_authenticated = False

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU2())
    from app.models import User

    monkeypatch.setattr(
        User, "verify_reset_password_token", staticmethod(lambda t: None)
    )
    r2 = client.get("/auth/reset_password/abc")
    assert r2.status_code in (302, 303)

    class V:
        def set_password(self, p):
            self.p = p

    monkeypatch.setattr(
        User, "verify_reset_password_token", staticmethod(lambda t: V())
    )
    from app import db

    db.session.commit.return_value = None
    r3 = client.post(
        "/auth/reset_password/abc",
        data={"password": "x", "password2": "x"},
        follow_redirects=False,
    )
    assert r3.status_code in (302, 303)

def test_verify_password_success(app, monkeypatch):
    from app.api import auth as auth_mod
    from app import db

    class U:
        def check_password(self, p):
            return p == "good"

    db.session.scalar.return_value = U()

    user = auth_mod.verify_password("alice", "good")

    assert user is not None


def test_verify_password_failure(app, monkeypatch):
    from app.api import auth as auth_mod
    from app import db

    db.session.scalar.return_value = None
    assert auth_mod.verify_password("alice", "bad") is None


def test_verify_token_success_and_failure(app, monkeypatch):
    from app.api import auth as auth_mod
    from app.models import User

    monkeypatch.setattr(User, "check_token", staticmethod(lambda token: "user"))
    assert auth_mod.verify_token("tok") == "user"

    monkeypatch.setattr(User, "check_token", staticmethod(lambda token: None))
    assert auth_mod.verify_token("tok") is None


def test_error_handlers_return_json(app):
    from app.api import auth as auth_mod

    r = auth_mod.basic_auth_error(401)
    if isinstance(r, tuple):
        payload, status = r
    else:
        payload, status = r.get_json(), r.status_code

    assert status == 401 and "error" in payload

    r = auth_mod.token_auth_error(401)
    if isinstance(r, tuple):
        payload, status = r
    else:
        payload, status = r.get_json(), r.status_code

    assert status == 401 and "error" in payload

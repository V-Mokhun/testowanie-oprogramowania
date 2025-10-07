from base64 import b64encode


def test_post_tokens_success_and_unauthorized(client, monkeypatch):
    from app.api import auth as auth_mod
    from app import db

    class U:
        def get_token(self):
            return "abc"

    auth_mod.basic_auth.verify_password_callback = lambda u, p: U()
    db.session.commit.return_value = None

    cred = b64encode(b"user:pass").decode("utf-8")
    r = client.post("/api/tokens", headers={"Authorization": f"Basic {cred}"})
    assert r.status_code in (200, 201)
    assert "token" in r.get_json()

    auth_mod.basic_auth.verify_password_callback = lambda u, p: None
    r2 = client.post("/api/tokens")
    assert r2.status_code in (401, 403)


def test_delete_tokens_success_and_unauthorized(client, monkeypatch):
    from app.api import auth as auth_mod
    from app import db

    called = {"revoked": False}

    class U:
        def revoke_token(self):
            called["revoked"] = True

    auth_mod.token_auth.verify_token_callback = lambda t: U()
    db.session.commit.return_value = None

    r = client.delete("/api/tokens", headers={"Authorization": "Bearer abc"})
    assert r.status_code == 204 and called["revoked"]

    auth_mod.token_auth.verify_token_callback = lambda t: None
    r2 = client.delete("/api/tokens")
    assert r2.status_code in (401, 403)

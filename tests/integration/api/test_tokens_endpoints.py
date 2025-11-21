from base64 import b64encode
from app import db
from app.models import User


def test_post_tokens(client):
    user = User(username="u", email="u@example.com")
    user.set_password("testpass")
    db.session.add(user)
    db.session.commit()

    cred = b64encode(b"u:testpass").decode("utf-8")
    r = client.post("/api/tokens", headers={"Authorization": f"Basic {cred}"})
    assert r.status_code == 200
    assert "token" in r.get_json()

    r2 = client.post("/api/tokens")
    assert r2.status_code == 401

    wrong_cred = b64encode(b"u:wrongpass").decode("utf-8")
    r3 = client.post("/api/tokens", headers={"Authorization": f"Basic {wrong_cred}"})
    assert r3.status_code == 401


def test_delete_tokens(client, user, auth_headers):
    r = client.delete("/api/tokens", headers=auth_headers)
    assert r.status_code == 204

    r2 = client.delete("/api/tokens")
    assert r2.status_code == 401

    r3 = client.delete("/api/tokens", headers={"Authorization": "Bearer invalid-token"})
    assert r3.status_code == 401

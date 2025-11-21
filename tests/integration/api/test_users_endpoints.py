import json
from app import db
from app.models import User


def test_create_user(client):
    payload = {"username": "u1", "email": "u1@example.com", "password": "P@ssw0rd"}
    r = client.post(
        "/api/users", data=json.dumps(payload), content_type="application/json"
    )
    assert r.status_code == 201
    user = db.session.get(User, r.get_json()["id"])
    assert user.username == "u1"
    assert user.email == "u1@example.com"
    assert user.check_password("P@ssw0rd")


def test_create_user_duplicates(client):
    payload = {"username": "u1", "email": "u1@example.com", "password": "P@ssw0rd"}
    r = client.post(
        "/api/users", data=json.dumps(payload), content_type="application/json"
    )
    assert r.status_code == 201
    assert r.get_json()["username"] == "u1"

    r2 = client.post(
        "/api/users", data=json.dumps(payload), content_type="application/json"
    )
    assert r2.status_code == 400

    payload2 = {"username": "u2", "email": "u1@example.com", "password": "P@ssw0rd"}
    r3 = client.post(
        "/api/users", data=json.dumps(payload2), content_type="application/json"
    )
    assert r3.status_code == 400


def test_get_user(client, user, auth_headers):
    r = client.get(f"/api/users/{user.id}")
    assert r.status_code == 401

    r2 = client.get(f"/api/users/{user.id}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.get_json()["username"] == user.username


def test_get_followers_and_following(client, user, auth_headers):
    user2 = User(username="testuser2", email="testuser2@example.com")
    user2.set_password("testpass2")
    db.session.add(user2)
    db.session.commit()

    r1 = client.get(f"/api/users/{user.id}/followers", headers=auth_headers)
    r2 = client.get(f"/api/users/{user.id}/following", headers=auth_headers)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.get_json()["items"] == [] and r2.get_json()["items"] == []


def test_update_user(client, user, auth_headers):
    user2 = User(username="testuser2", email="testuser2@example.com")
    user2.set_password("testpass2")
    db.session.add(user2)
    db.session.commit()
    token2 = user2.get_token()
    db.session.commit()
    auth_headers2 = {"Authorization": f"Bearer {token2}"}

    r_ok = client.put(
        f"/api/users/{user.id}",
        data=json.dumps({"username": "new", "email": "n@example.com"}),
        content_type="application/json",
        headers=auth_headers,
    )
    assert r_ok.status_code == 200
    user_updated = db.session.get(User, user.id)
    assert user_updated.username == "new"
    assert user_updated.email == "n@example.com"

    r_dup = client.put(
        f"/api/users/{user.id}",
        data=json.dumps({"username": "testuser2"}),
        content_type="application/json",
        headers=auth_headers,
    )
    assert r_dup.status_code == 400

    r_403 = client.put(
        f"/api/users/{user.id}",
        data=json.dumps({"username": "new", "email": "n@example.com"}),
        content_type="application/json",
        headers=auth_headers2,
    )
    assert r_403.status_code == 403

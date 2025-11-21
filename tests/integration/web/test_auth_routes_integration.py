import sqlalchemy as sa
from app import db
from app.models import User
from tests.conftest import login_user_via_client, is_logged_in


def test_login_redirect_when_authenticated(client, user):
    login_user_via_client(client, "testuser", "testpass")
    r = client.get("/auth/login")
    assert r.status_code == 302


def test_login(client):
    client.post(
        "/auth/login",
        data={"username": "nonexistent", "password": "p"},
        follow_redirects=False,
    )
    assert not is_logged_in(client)

    user = User(username="u", email="u@example.com")
    user.set_password("p")
    db.session.add(user)
    db.session.commit()

    client.post(
        "/auth/login?next=/index",
        data={"username": "u", "password": "p", "remember_me": "y"},
        follow_redirects=False,
    )
    assert is_logged_in(client)


def test_logout(client, user):
    login_user_via_client(client, "testuser", "testpass")
    client.get("/auth/logout")
    assert not is_logged_in(client)


def test_register_redirect_when_authenticated(client, user):
    login_user_via_client(client, "testuser", "testpass")
    r = client.get("/auth/register")
    assert r.status_code == 302


def test_register(client):
    client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "p",
            "password2": "p",
        },
        follow_redirects=False,
    )

    user = db.session.scalar(sa.select(User).where(User.username == "newuser"))
    assert user is not None
    assert user.email == "newuser@example.com"


def test_reset_password_with_token(client, user):
    user = db.session.get(User, user.id)
    assert user.check_password("testpass")

    token = user.get_reset_password_token()
    client.post(
        f"/auth/reset_password/{token}",
        data={"password": "newpass", "password2": "newpass"},
        follow_redirects=False,
    )

    user_updated = db.session.get(User, user.id)
    assert user_updated.check_password("newpass")

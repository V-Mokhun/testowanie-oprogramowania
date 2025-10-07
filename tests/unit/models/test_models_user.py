from datetime import datetime, timezone
from app.models import User
from app.models import Notification
import sqlalchemy as sa


def test_password_hash_and_check(app):
    u = User(username="alice", email="alice@example.com")
    u.set_password("secret")
    assert u.check_password("secret")
    assert not u.check_password("wrong")


def test_avatar_url_generation(app):
    u = User(username="bob", email="Bob@Example.com")
    url = u.avatar(80)
    assert url.startswith("https://www.gravatar.com/avatar/")
    assert "s=80" in url


def test_to_dict_and_from_dict_roundtrip(app, monkeypatch):
    u = User(username="carol", email="carol@example.com")
    u.set_password("Password1!")

    u.last_seen = datetime.now(timezone.utc)

    monkeypatch.setattr(u, "posts_count", lambda: 2)
    monkeypatch.setattr(u, "followers_count", lambda: 3)
    monkeypatch.setattr(u, "following_count", lambda: 4)

    u.id = 1
    with app.test_request_context("/"):
        data = u.to_dict(include_email=True)
    assert data["username"] == "carol"
    assert data["post_count"] == 2
    assert data["follower_count"] == 3
    assert data["following_count"] == 4
    assert data["email"] == "carol@example.com"

    u2 = User()
    u2.from_dict(
        {
            "username": "c2",
            "email": "c2@example.com",
            "about_me": "hi",
            "password": "x",
        },
        new_user=True,
    )
    assert u2.username == "c2"
    assert u2.email == "c2@example.com"
    assert u2.about_me == "hi"
    assert u2.check_password("x")


def test_get_token_and_check_token(app, monkeypatch):
    u = User(username="dave", email="dave@example.com")

    from app import db

    db.session.scalar.return_value = u

    token = u.get_token(expires_in=10)
    assert isinstance(token, str)

    got = User.check_token(token)
    assert got is u


def test_get_token_reuse_and_expiration(app, monkeypatch):
    u = User(username="erin", email="erin@example.com")
    from app import db

    db.session.scalar.return_value = u

    token1 = u.get_token(expires_in=3600)
    token2 = u.get_token(expires_in=3600)
    assert token2 == token1

    u.token_expiration = u.token_expiration.replace(microsecond=0)
    past = u.token_expiration
    u.token_expiration = past.replace(year=past.year - 1)
    assert User.check_token(token1) is None


def test_revoke_token(app, monkeypatch):
    u = User(username="frank", email="frank@example.com")
    from app import db

    db.session.scalar.return_value = u
    token = u.get_token(expires_in=10)
    assert User.check_token(token) is u
    u.revoke_token()
    assert User.check_token(token) is None


def test_reset_password_token_roundtrip(app, monkeypatch):
    u = User(username="grace", email="grace@example.com")

    from app import db

    def _get(model, ident):
        return u

    db.session.get = _get

    token = u.get_reset_password_token(expires_in=60)
    got = User.verify_reset_password_token(token)
    assert got is u


def test_follow_and_unfollow_without_errors(app, monkeypatch):
    follower = User(username="ann", email="ann@example.com")
    followed = User(username="ben", email="ben@example.com")

    monkeypatch.setattr(follower, "is_following", lambda u: False)
    follower.follow(followed)

    monkeypatch.setattr(follower, "is_following", lambda u: True)
    follower.unfollow(followed)


def test_add_notification_creates_notification_and_get_data(app, monkeypatch):
    u = User(username="z", email="z@example.com")

    executed = {"called": False}
    added = {"obj": None}

    from app import db

    db.session.execute.side_effect = lambda *a, **k: executed.update(called=True)
    db.session.add.side_effect = lambda obj: added.update(obj=obj)

    payload = {"a": 1, "b": "c"}
    n = u.add_notification("test", payload)

    assert isinstance(n, Notification)
    assert added["obj"] is n
    assert executed["called"] is True
    assert n.get_data() == payload


def test_user_following_posts_returns_select(app):
    u = User(username="sel", email="sel@example.com")
    stmt = u.following_posts()
    assert isinstance(stmt, sa.Select)
    assert any(
        getattr(o.element, "name", "") == "timestamp" for o in stmt._order_by_clauses
    )


def test_user_get_tasks_in_progress_and_get_task_in_progress(app, monkeypatch):
    u = User(username="t", email="t@example.com")

    from app import db

    db.session.scalars.return_value = iter(["task1", "task2"])
    assert list(u.get_tasks_in_progress()) == ["task1", "task2"]

    db.session.scalar.return_value = "taskx"
    assert u.get_task_in_progress("export_posts") == "taskx"


def test_user_launch_task_enqueues_and_returns_task(app, monkeypatch):
    u = User(username="worker", email="w@example.com")
    u.id = 7

    class Job:
        def get_id(self):
            return "jid-1"

    from flask import current_app

    current_app.task_queue.enqueue = lambda *a, **k: Job()
    added = {"obj": None}
    from app import db

    db.session.add.side_effect = lambda obj: added.update(obj=obj)
    task = u.launch_task("export_posts", "desc")
    assert task.id == "jid-1"
    assert added["obj"] is task

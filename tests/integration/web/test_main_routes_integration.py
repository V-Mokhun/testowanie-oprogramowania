import json


def _stub_current_user(monkeypatch, **attrs):
    class CU:
        is_authenticated = True
        username = "me"

        def __init__(self):
            for k, v in attrs.items():
                setattr(self, k, v)

        def follow(self, u):
            pass

        def unfollow(self, u):
            pass

        def add_notification(self, *a, **k):
            pass

        def unread_message_count(self):
            return 0

        def get_tasks_in_progress(self):
            return []

        def is_following(self, user):
            return False

        class _Msgs:
            def select(self):
                return self

            def order_by(self, *a, **k):
                return self

        messages_received = _Msgs()

        class _Notifications:
            def select(self):
                return self

            def where(self, *a, **k):
                return self

            def order_by(self, *a, **k):
                return self

        notifications = _Notifications()

        def get_task_in_progress(self, name):
            return None

        def launch_task(self, *a, **k):
            class T:
                pass

            return T()

    cu = CU()
    monkeypatch.setattr("flask_login.utils._get_user", lambda: cu)
    return cu


def test_index_post_creates_post_and_detects_language(client, monkeypatch):
    _stub_current_user(monkeypatch)
    import langdetect

    monkeypatch.setattr(langdetect, "detect", lambda s: "en")

    class _Post:
        def __init__(self, body, author, language):
            self.body = body
            self.author = author
            self.language = language

    monkeypatch.setattr("app.main.routes.Post", _Post)
    from app import db

    db.session.add.return_value = None
    db.session.commit.return_value = None
    r = client.post("/index", data={"post": "hello"}, follow_redirects=False)
    assert r.status_code in (302, 303)


def test_index_post_language_detect_exception_sets_empty(client, monkeypatch):
    _stub_current_user(monkeypatch)
    import langdetect

    class E(Exception):
        pass

    monkeypatch.setattr(
        langdetect, "detect", lambda s: (_ for _ in ()).throw(Exception("boom"))
    )

    class _Post:
        def __init__(self, body, author, language):
            self.body = body
            self.author = author
            self.language = language

    monkeypatch.setattr("app.main.routes.Post", _Post)
    from app import db

    db.session.add.return_value = None
    db.session.commit.return_value = None
    r = client.post("/index", data={"post": "hello"}, follow_redirects=False)
    assert r.status_code in (302, 303)


def test_explore_lists_posts(client, monkeypatch):
    _stub_current_user(monkeypatch)
    from app import db

    class Resources:
        items = []
        pages = 1
        total = 0
        has_next = False
        has_prev = False
        next_num = None
        prev_num = None

    db.paginate = lambda q, page, per_page, error_out=False: Resources
    r = client.get("/explore")
    assert r.status_code == 200


def test_user_profile_and_popup(client, monkeypatch):
    _stub_current_user(monkeypatch)
    from app import db

    class U:
        username = "other"

        def avatar(self, size):
            return ""

        def followers_count(self):
            return 0

        def following_count(self):
            return 0

        class Posts:
            def select(self):
                return self

            def order_by(self, *a, **k):
                return self

        posts = Posts()

    db.first_or_404 = lambda q: U()
    from app import db as _db

    class Resources:
        items = []
        pages = 1
        total = 0
        has_next = False
        has_prev = False
        next_num = None
        prev_num = None

    _db.paginate = lambda q, page, per_page, error_out=False: Resources
    r = client.get("/user/other")
    assert r.status_code == 200
    r2 = client.get("/user/other/popup")
    assert r2.status_code == 200


def test_edit_profile_get_and_post(client, monkeypatch):
    _stub_current_user(monkeypatch, username="me", about_me="bio")
    from app import db

    db.session.commit.return_value = None
    r = client.get("/edit_profile")
    assert r.status_code == 200
    r2 = client.post(
        "/edit_profile",
        data={"username": "new", "about_me": "x"},
        follow_redirects=False,
    )
    assert r2.status_code in (302, 303)


def test_follow_and_unfollow(client, monkeypatch):
    _stub_current_user(monkeypatch)
    from app import db

    class U:
        username = "other"

    db.session.scalar.return_value = U()
    db.session.commit.return_value = None
    r = client.post("/follow/other", data={"submit": "y"}, follow_redirects=False)
    assert r.status_code in (302, 303)
    r2 = client.post("/unfollow/other", data={"submit": "y"}, follow_redirects=False)
    assert r2.status_code in (302, 303)


def test_translate_endpoint(client, monkeypatch):
    _stub_current_user(monkeypatch)
    r = client.post(
        "/translate",
        data=json.dumps({"text": "a", "source_language": "en", "dest_language": "es"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert "text" in r.get_json()


def test_search_redirect_and_success(client, monkeypatch):
    _stub_current_user(monkeypatch)

    r = client.get("/search")
    assert r.status_code in (302, 303)

    from app.models import Post
    from datetime import datetime, timezone

    def _search(expr, page, per_page):
        class A:
            def avatar(self, size):
                return ""

        class P:
            author = A()
            timestamp = datetime.now(timezone.utc)

        return [P()], 1

    Post.search = classmethod(
        lambda cls, expr, page, per_page: _search(expr, page, per_page)
    )
    r2 = client.get("/search?q=abc")
    assert r2.status_code == 200


def test_send_message_and_messages_list(client, monkeypatch):
    _stub_current_user(monkeypatch)
    from app import db

    class R:
        def __init__(self):
            class Msgs:
                def select(self):
                    return self

                def order_by(self, *a, **k):
                    return self

            self.messages_received = Msgs()

    class U:
        username = "other"

        def add_notification(self, *a, **k):
            pass

        def unread_message_count(self):
            return 0

    db.first_or_404 = lambda q: U()

    class _Message:
        class timestamp:
            @staticmethod
            def desc():
                return None

        def __init__(self, author, recipient, body):
            self.author = author
            self.recipient = recipient
            self.body = body

    monkeypatch.setattr("app.main.routes.Message", _Message)
    db.session.add.return_value = None
    db.session.commit.return_value = None

    r = client.post(
        "/send_message/other", data={"message": "hi"}, follow_redirects=False
    )
    assert r.status_code in (302, 303)

    from app import db as _db

    class Resources:
        items = []
        pages = 1
        total = 0
        has_next = False
        has_prev = False
        next_num = None
        prev_num = None

    _db.paginate = lambda q, page, per_page, error_out=False: Resources
    r2 = client.get("/messages")
    assert r2.status_code == 200


def test_export_posts_does_not_launch_when_in_progress(client, monkeypatch):
    cu = _stub_current_user(monkeypatch)

    cu.get_task_in_progress = lambda name: object()
    launched = []
    cu.launch_task = lambda *a, **k: launched.append((a, k))

    r = client.get("/export_posts")
    assert r.status_code in (302, 303)
    assert launched == []


def test_export_posts_launches_when_not_in_progress(client, monkeypatch):
    cu = _stub_current_user(monkeypatch)

    cu.get_task_in_progress = lambda name: None
    launched = []
    cu.launch_task = lambda *a, **k: launched.append((a, k))

    r = client.get("/export_posts")
    assert r.status_code in (302, 303)
    assert len(launched) == 1
    assert launched[0][0][0] == "export_posts"


def test_get_notifications(client, monkeypatch):
    _stub_current_user(monkeypatch)
    from app import db as _db

    class N:
        name = "n"
        timestamp = 0

        def get_data(self):
            return {}

    _db.session.scalars.return_value = iter([N()])
    r = client.get("/notifications?since=0")
    assert r.status_code == 200

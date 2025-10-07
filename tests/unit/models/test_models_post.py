from app.models import Post, SearchableMixin


def test_post_repr(app):
    p = Post(body="hello")
    assert "Post" in repr(p)
    assert "hello" in repr(p)


def test_search_returns_ids_and_total_when_hits_exist(app, monkeypatch):
    monkeypatch.setattr(Post, "search", classmethod(SearchableMixin.search.__func__))

    ids = [3, 1, 2]
    total = 3

    monkeypatch.setattr("app.models.query_index", lambda *a, **k: (ids, total))

    posts = [Post(body=f"#{i}") for i in ids]

    from app import db

    db.session.scalars.return_value = iter(posts)

    items, got_total = Post.search("query", page=1, per_page=10)

    items_list = list(items)
    assert got_total == total
    assert len(items_list) == 3
    assert [p.body for p in items_list] == ["#3", "#1", "#2"]

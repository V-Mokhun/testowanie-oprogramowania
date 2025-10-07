from app import db
from app.models import Post, SearchableMixin


def test_search_returns_empty_when_total_zero(app, monkeypatch):
    monkeypatch.setattr("app.models.query_index", lambda *args, **kwargs: ([], 0))

    monkeypatch.setattr(Post, "search", classmethod(SearchableMixin.search.__func__))

    items, total = Post.search("anything", page=1, per_page=10)
    assert items == []
    assert total == 0


def test_before_after_commit_triggers_indexing(app, monkeypatch):
    added = []
    removed = []

    def _add_to_index(index, model):
        added.append((index, model))

    def _remove_from_index(index, model):
        removed.append((index, model))

    monkeypatch.setattr("app.models.add_to_index", _add_to_index)
    monkeypatch.setattr("app.models.remove_from_index", _remove_from_index)

    class Dummy(SearchableMixin):
        __tablename__ = "dummy"
        __searchable__ = ["field"]
        id = 123
        field = "x"

    d = Dummy()

    session = db.session
    session._changes = {"add": [d], "update": [d], "delete": [d]}

    SearchableMixin.after_commit(session)

    assert ("dummy", d) in added
    assert ("dummy", d) in removed


def test_reindex_calls_add_to_index_for_each_instance(app, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.search.add_to_index", lambda index, model: calls.append((index, model))
    )

    monkeypatch.setattr(
        "app.models.add_to_index", lambda index, model: calls.append((index, model))
    )

    p1 = Post(body="a")
    p1.id = 1
    p2 = Post(body="b")
    p2.id = 2
    db.session.scalars.return_value = iter([p1, p2])

    with app.app_context():
        Post.reindex()

    assert len(calls) == 2
    assert all(call[0] == "post" for call in calls)

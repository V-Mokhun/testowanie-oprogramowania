from app.search import add_to_index, remove_from_index, query_index


def test_add_to_index_builds_payload_and_calls_es_index(app):
    class M:
        __searchable__ = ["body", "lang"]
        id = 5
        body = "text"
        lang = "en"

    add_to_index("post", M())
    es = app.elasticsearch
    es.index.assert_called()
    args, kwargs = es.index.call_args
    assert kwargs["index"] == "post"
    assert kwargs["id"] == 5
    assert kwargs["document"] == {"body": "text", "lang": "en"}


def test_remove_from_index_calls_es_delete(app):
    class M:
        id = 7

    remove_from_index("post", M())
    es = app.elasticsearch
    es.delete.assert_called()
    args, kwargs = es.delete.call_args
    assert kwargs["index"] == "post"
    assert kwargs["id"] == 7


def test_query_index_returns_ids_and_total(app, monkeypatch):
    app.elasticsearch.search.return_value = {
        "hits": {"hits": [{"_id": "1"}, {"_id": "2"}], "total": {"value": 2}}
    }
    ids, total = query_index("post", "q", 2, 10)
    assert ids == [1, 2]
    assert total == 2


def test_query_index_when_es_none_returns_empty(app, monkeypatch):
    app.elasticsearch = None
    ids, total = query_index("post", "q", 1, 10)
    assert ids == [] and total == 0

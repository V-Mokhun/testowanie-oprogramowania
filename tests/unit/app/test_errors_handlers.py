def test_not_found_html_vs_json(app):
    from app.errors import handlers as h

    with app.test_request_context("/missing", headers={"Accept": "text/html"}):
        resp, status = h.not_found_error(Exception())
        assert status == 404
        assert hasattr(resp, "split")

    with app.test_request_context("/missing", headers={"Accept": "application/json"}):
        payload, status = h.not_found_error(Exception())
        assert status == 404 and "error" in payload


def test_internal_error_html_vs_json_rolls_back(app, monkeypatch):
    from app.errors import handlers as h
    from app import db

    rolled = {"v": False}
    db.session.rollback.side_effect = lambda: rolled.__setitem__("v", True)

    with app.test_request_context("/boom", headers={"Accept": "text/html"}):
        resp, status = h.internal_error(Exception())
        assert status == 500 and rolled["v"] is True

    with app.test_request_context("/boom", headers={"Accept": "application/json"}):
        payload, status = h.internal_error(Exception())
        assert status == 500 and "error" in payload

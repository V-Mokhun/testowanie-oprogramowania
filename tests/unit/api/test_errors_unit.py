from app.api import errors as err


def test_error_response(app):
    payload, status = err.error_response(404, "missing")
    assert status == 404
    assert payload["error"] and payload["message"] == "missing"


def test_bad_request(app):
    payload, status = err.bad_request("nope")
    assert status == 400 and payload["message"] == "nope"


def test_http_exception_handler(app):
    class E(Exception):
        code = 403

    payload, status = err.handle_exception(E())
    assert status == 403 and "error" in payload

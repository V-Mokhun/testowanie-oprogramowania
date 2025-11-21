def test_error_response_and_bad_request(app):
    from app.api import errors as err

    payload, status = err.error_response(404, "missing")
    assert status == 404
    assert payload["error"] and payload["message"] == "missing"

    payload, status = err.bad_request("nope")
    assert status == 400 and payload["message"] == "nope"


def test_http_exception_handler(app):
    from app.api import errors as err

    class E(Exception):
        code = 403

    payload, status = err.handle_exception(E())
    assert status == 403 and "error" in payload

def test_translate_requires_config_key(app):
    import importlib
    import app.translate as tmod

    tmod = importlib.reload(tmod)
    app.config["MS_TRANSLATOR_KEY"] = ""
    msg = tmod.translate("hi", "en", "es")
    assert "not configured" in msg.lower()


def test_translate_success_and_failure(app, monkeypatch):
    import importlib
    import app.translate as tmod

    tmod = importlib.reload(tmod)
    app.config["MS_TRANSLATOR_KEY"] = "k"

    class R:
        def __init__(self, status_code, data=None):
            self.status_code = status_code
            self._data = data or [{"translations": [{"text": "hola"}]}]

        def json(self):
            return self._data

    monkeypatch.setattr(
        tmod,
        "requests",
        type("Req", (), {"post": staticmethod(lambda *a, **k: R(200))}),
    )
    assert tmod.translate("hi", "en", "es") == "hola"

    monkeypatch.setattr(
        tmod,
        "requests",
        type("Req", (), {"post": staticmethod(lambda *a, **k: R(500))}),
    )
    assert "failed" in tmod.translate("hi", "en", "es")

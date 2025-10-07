from unittest.mock import Mock
from app.email import send_email


def test_send_email_sync_calls_mail_send(app, monkeypatch):
    import app.email as email_mod

    called = {"n": 0}

    def _send(msg):
        called["n"] += 1
        assert msg.subject == "subj"
        assert msg.sender == "s@example.com"
        assert msg.recipients == ["r@example.com"]
        assert "text" in msg.body
        assert "html" in msg.html

    email_mod.mail = Mock(send=_send)

    send_email(
        "subj",
        "s@example.com",
        ["r@example.com"],
        "text body",
        "html body",
        attachments=None,
        sync=True,
    )
    assert called["n"] == 1


def test_send_email_async_uses_thread_with_app_context(app, monkeypatch):
    import app.email as email_mod

    started = {"args": None}

    class FakeThread:
        def __init__(self, target, args):
            started["args"] = (target, args)

        def start(self):
            target, (app_obj, msg) = started["args"]
            email_mod.mail = Mock(send=Mock())
            target(app_obj, msg)

    monkeypatch.setattr(email_mod, "Thread", FakeThread)
    send_email(
        "s", "s@example.com", ["r@example.com"], "t", "h", attachments=None, sync=False
    )


def test_send_email_attachments_attached(app):
    import app.email as email_mod

    attached = {"files": []}

    def _attach(filename, mimetype, data):
        attached["files"].append((filename, mimetype, data))

    class SpyMessage:
        def __init__(self, subject, sender, recipients):
            self.subject = subject
            self.sender = sender
            self.recipients = recipients
            self.body = ""
            self.html = ""

        def attach(self, *args):
            _attach(*args)

    email_mod.Message = SpyMessage
    email_mod.mail = Mock(send=Mock())
    send_email(
        "s",
        "s@example.com",
        ["r@example.com"],
        "t",
        "h",
        attachments=[("a.txt", "text/plain", "A")],
        sync=True,
    )
    assert attached["files"] == [("a.txt", "text/plain", "A")]

from app.models import Message


def test_message_repr(app):
    m = Message(body="hello")
    assert "Message" in repr(m) and "hello" in repr(m)

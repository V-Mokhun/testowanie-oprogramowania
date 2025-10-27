import os
import sys
import types
from unittest.mock import Mock, MagicMock
import pytest

# Ensure project root is on sys.path for 'app' package imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db as _db
from config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ELASTICSEARCH_URL = None
    REDIS_URL = None
    POSTS_PER_PAGE = 3
    SECRET_KEY = "test"


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app


@pytest.fixture(autouse=True)
def mock_db(app, monkeypatch):
    fake_session = MagicMock()
    fake_session.add = MagicMock()
    fake_session.commit = MagicMock()
    fake_session.rollback = MagicMock()
    fake_session.delete = MagicMock()
    fake_session.execute = MagicMock()
    fake_session.scalar = MagicMock(return_value=None)
    fake_session.scalars = MagicMock(return_value=iter(()))

    _db.session = fake_session

    def _paginate_stub(query, page=1, per_page=10, error_out=False):
        return types.SimpleNamespace(
            items=[],
            pages=1,
            total=0,
            has_next=False,
            has_prev=False,
            next_num=None,
            prev_num=None,
        )

    def _get_or_404_stub(model, ident):
        raise Exception("get_or_404 called without explicit patch in test")

    def _first_or_404_stub(statement):
        raise Exception("first_or_404 called without explicit patch in test")

    monkeypatch.setattr(_db, "paginate", _paginate_stub, raising=True)
    monkeypatch.setattr(_db, "get_or_404", _get_or_404_stub, raising=True)
    monkeypatch.setattr(_db, "first_or_404", _first_or_404_stub, raising=True)

    yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_external_services(app, monkeypatch):
    fake_es = Mock()
    fake_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}
    fake_es.index.return_value = {"_id": "1"}
    fake_es.delete.return_value = {"result": "deleted"}
    app.elasticsearch = fake_es

    fake_queue = Mock()
    fake_job = Mock()
    fake_job.get_id.return_value = "job-id"
    fake_job.meta = {}
    fake_queue.enqueue.return_value = fake_job
    app.task_queue = fake_queue

    monkeypatch.setattr(
        "rq.job.Job.fetch", classmethod(lambda cls, _id, connection=None: fake_job)
    )

    import app.email as email_mod

    email_mod.mail = Mock(send=Mock())

    monkeypatch.setattr(
        "app.translate.translate", lambda text, s, d: f"{text} [{s}->{d}]"
    )
    try:
        import langdetect

        monkeypatch.setattr(langdetect, "detect", lambda _: "en")
    except Exception:
        pass

    yield

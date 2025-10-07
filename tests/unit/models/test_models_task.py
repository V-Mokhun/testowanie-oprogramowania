from unittest.mock import Mock
from app.models import Task


def test_get_rq_job_returns_none_on_errors(app, monkeypatch):
    t = Task(id="job-id", name="export_posts")

    import rq

    def _raise(*args, **kwargs):
        raise rq.exceptions.NoSuchJobError

    monkeypatch.setattr(
        "rq.job.Job.fetch", classmethod(lambda cls, *_a, **_k: _raise())
    )

    assert t.get_rq_job() is None


def test_get_progress_uses_job_meta(app, monkeypatch):
    t = Task(id="job-id", name="export_posts")

    fake_job = Mock()
    fake_job.meta = {"progress": 42}
    monkeypatch.setattr(
        "rq.job.Job.fetch", classmethod(lambda cls, *_a, **_k: fake_job)
    )

    assert t.get_progress() == 42


def test_get_progress_defaults_to_100_when_job_missing(app, monkeypatch):
    t = Task(id="job-id", name="export_posts")

    import rq

    def _raise(*args, **kwargs):
        raise rq.exceptions.NoSuchJobError

    monkeypatch.setattr(
        "rq.job.Job.fetch", classmethod(lambda cls, *_a, **_k: _raise())
    )

    assert t.get_progress() == 100

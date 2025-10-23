"""
E2E-specific conftest that doesn't inherit global mocking.
This ensures E2E tests use real database with seeded data.
"""
import contextlib
import socket
import threading
import time

import pytest


@pytest.fixture(scope="session")
def app_instance():
    """Create a real Flask app instance for E2E tests."""
    import os
    import sys
    
    # Add the project root to the Python path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app
    from config import Config
    
    class E2EConfig(Config):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        WTF_CSRF_ENABLED = False
        TESTING = True
    
    app = create_app(E2EConfig)
    return app


@pytest.fixture(scope="session", autouse=True)
def seed_database(app_instance):
    """Seed the database with test data before running E2E tests."""
    from seed_data import seed_test_data
    seed_test_data(app_instance)
    yield


@pytest.fixture(scope="session")
def free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(app_instance, free_port):
    def run():
        app_instance.run(host="127.0.0.1", port=free_port, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(0.5)
    yield f"http://127.0.0.1:{free_port}"


@pytest.fixture(scope="session")
def browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Prefer Selenium Manager (no network) and fall back to webdriver-manager only if needed
    try:
        driver = webdriver.Chrome(options=options)
    except Exception:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    driver.set_window_size(1366, 900)
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def e2e_stub_current_user(monkeypatch):
    class CU:
        is_authenticated = True
        username = "testuser"  # Use the seeded test user
        about_me = "Test user bio"
        last_seen = None
        
        def __eq__(self, other):
            """Enable comparison with User objects in templates."""
            if hasattr(other, 'username'):
                return self.username == other.username
            return False

        def unread_message_count(self, *args, **kwargs):
            return 0

        def get_tasks_in_progress(self):
            return []

        def get_task_in_progress(self, name):
            return None

        def launch_task(self, *a, **k):
            class T:
                id = "t1"
            return T()

        def is_following(self, user):
            return False  # Default to not following

        def following_posts(self):
            class MockQuery:
                def paginate(self, page, per_page, error_out=False):
                    return type('Paginated', (), {
                        'items': [],
                        'pages': 1,
                        'total': 0,
                        'has_next': False,
                        'has_prev': False,
                        'next_num': None,
                        'prev_num': None,
                    })()
            return MockQuery()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: CU())
    yield

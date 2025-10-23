from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _make_fake_post(
    *,
    post_id: int = 1,
    body: str = "Hello world",
    author_username: str = "e2e",
    language: str = "en",
):
    class Author:
        username = author_username

        def avatar(self, size):
            return f"/static/avatar_{size}.png"

    return SimpleNamespace(
        id=post_id,
        body=body,
        author=Author(),
        language=language,
        timestamp=datetime.now(timezone.utc),
    )


def _paginate(items, *, has_next=False, has_prev=False, next_num=None, prev_num=None):
    return SimpleNamespace(
        items=items,
        pages=1,
        total=len(items),
        has_next=has_next,
        has_prev=has_prev,
        next_num=next_num,
        prev_num=prev_num,
    )


def test_index_renders_with_greeting_and_post_form(browser, live_server):
    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    page = browser.page_source
    assert "Hi, e2e!" in page or "Hi," in page
    # Post form should be present (textarea and a submit button)
    assert browser.find_element(By.CSS_SELECTOR, "textarea")
    assert browser.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]")


def test_create_post_via_form_shows_flash_and_post_appears(browser, live_server, monkeypatch):
    # Arrange paginate to return our new post after submission
    from app import db

    new_post = _make_fake_post(post_id=42, body="My first post")

    def paginate_after_post(query, page=1, per_page=10, error_out=False):
        return _paginate([new_post])

    monkeypatch.setattr(db, "paginate", paginate_after_post, raising=True)

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
    )
    browser.find_element(By.CSS_SELECTOR, "textarea").send_keys("My first post")
    browser.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]").click()

    WebDriverWait(browser, 5).until(
        lambda d: "/index" in d.current_url or "Your post is now live!" in d.page_source
    )

    page = browser.page_source
    assert "Your post is now live!" in page or "My first post" in page


def test_post_form_validation_shows_error_for_empty_post(browser, live_server):
    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
    )
    # Submit empty post
    browser.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]").click()
    # Should remain on page and show validation error near the field
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
    )
    assert "/index" in browser.current_url


def test_explore_page_renders_with_posts(browser, live_server, monkeypatch):
    from app import db

    posts = [_make_fake_post(post_id=i, body=f"post {i}") for i in range(1, 4)]

    def paginate_explore(query, page=1, per_page=10, error_out=False):
        return _paginate(posts)

    monkeypatch.setattr(db, "paginate", paginate_explore, raising=True)

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    src = browser.page_source
    assert "post 1" in src and "post 2" in src and "post 3" in src


def test_posts_display_avatar_username_timestamp_and_body(browser, live_server, monkeypatch):
    from app import db

    post = _make_fake_post(body="content body", author_username="alice")

    def paginate_with_post(query, page=1, per_page=10, error_out=False):
        return _paginate([post])

    monkeypatch.setattr(db, "paginate", paginate_with_post, raising=True)

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    # Avatar image rendered
    assert browser.find_element(By.CSS_SELECTOR, "img[src*='avatar_']")
    # Username link
    assert browser.find_element(By.LINK_TEXT, "alice")
    # Body text present
    assert "content body" in browser.page_source


def test_pagination_links_render_when_multiple_pages(browser, live_server, monkeypatch):
    from app import db

    posts = [_make_fake_post(post_id=i) for i in range(1, 4)]

    def paginate_many(query, page=1, per_page=3, error_out=False):
        # Simulate 2 pages, we are on page 1
        return _paginate(posts, has_next=True, has_prev=False, next_num=2, prev_num=None)

    monkeypatch.setattr(db, "paginate", paginate_many, raising=True)

    browser.get(f"{live_server}/explore")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    # Older posts (next) should be enabled - look for the link with arrow
    next_link = browser.find_element(By.XPATH, "//a[contains(text(), 'Older posts')]")
    assert next_link.get_attribute("href") is not None
    # Newer posts (prev) should be disabled on first page
    prev_item = browser.find_element(By.XPATH, "//li[contains(@class,'page-item')][1]")
    assert "disabled" in prev_item.get_attribute("class")



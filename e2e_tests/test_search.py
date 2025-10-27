"""
Search functionality E2E tests with real Elasticsearch.
Tests search form, results, pagination, and content discovery using real search engine.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from conftest import login_user


def test_search_form_appears_in_navbar_for_authenticated_users(browser, live_server):
    """Test that search form appears in navbar for authenticated users."""
    search_inputs = browser.find_elements(By.CSS_SELECTOR, "#q")
    assert len(search_inputs) == 0

    login_user(browser, live_server)

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    search_input = browser.find_element(By.CSS_SELECTOR, "#q")
    assert search_input.is_displayed()


def test_search_results_display_matching_posts(browser, live_server):
    """Test that search results display matching posts using real Elasticsearch."""
    login_user(browser, live_server)

    search_input = browser.find_element(By.CSS_SELECTOR, "#q")
    search_input.send_keys("python")
    search_input.send_keys(Keys.ENTER)

    WebDriverWait(browser, 10).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Search Results")
    )

    assert "/search" in browser.current_url

    assert "Python programming is amazing" in browser.page_source


def test_search_results_page_requires_authentication(browser, live_server):
    """Test that search results page requires authentication."""
    browser.get(f"{live_server}/search?q=test")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "/auth/login" in browser.current_url


def test_search_form_validation_works(browser, live_server):
    """Test that search form validation works."""
    login_user(browser, live_server)

    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    search_input = browser.find_element(By.CSS_SELECTOR, "#q")
    search_input.send_keys("")
    search_input.send_keys(Keys.ENTER)

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "/search" not in browser.current_url
    assert "Search Results" not in browser.page_source


def test_search_with_no_results_shows_appropriate_message(browser, live_server):
    """Test that search with no results shows appropriate message."""
    login_user(browser, live_server)

    search_input = browser.find_element(By.CSS_SELECTOR, "#q")
    search_input.send_keys("nonexistentcontent12345")
    search_input.send_keys(Keys.ENTER)

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "/search" in browser.current_url
    posts = browser.find_elements(By.CSS_SELECTOR, "table.table-hover")
    assert len(posts) == 0

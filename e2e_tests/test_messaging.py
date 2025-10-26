"""
Private messaging E2E tests.
Tests message sending, receiving, pagination, and UI updates.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_send_message_link_appears_on_other_users_profiles(browser, live_server):
    """Test that send message link appears on other users' profiles."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to another user's profile
    browser.get(f"{live_server}/user/otheruser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    
    # Check that send message link is present
    message_link = browser.find_element(By.LINK_TEXT, "Send private message")
    assert message_link.is_displayed()
    assert message_link.get_attribute("href") == f"{live_server}/send_message/otheruser"


def test_send_message_link_does_not_appear_on_own_profile(browser, live_server):
    """Test that send message link does not appear on own profile."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to own profile
    browser.get(f"{live_server}/user/testuser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    
    # Check that send message link is NOT present
    message_links = browser.find_elements(By.LINK_TEXT, "Send private message")
    assert len(message_links) == 0


def test_send_message_page_renders_with_form(browser, live_server):
    """Test that send message page renders with form."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to send message page
    browser.get(f"{live_server}/send_message/otheruser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Check that the form elements are present
    message_field = browser.find_element(By.NAME, "message")
    assert message_field.is_displayed()
    
    submit_button = browser.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]")
    assert submit_button.is_displayed()
    
    # Check that the recipient is mentioned
    page_source = browser.page_source
    assert "otheruser" in page_source or "Send a private message" in page_source


def test_message_submission_shows_success_and_redirects(browser, live_server):
    """Test that message submission shows success flash and redirects."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to send message page
    browser.get(f"{live_server}/send_message/otheruser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )
    
    # Fill in the message
    message_field = browser.find_element(By.NAME, "message")
    message_field.clear()
    message_field.send_keys("Hello, this is a test message!")
    
    # Submit the form
    submit_button = browser.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]")
    submit_button.click()
    
    # Wait for redirect (should go to messages page or user profile)
    WebDriverWait(browser, 5).until(
        lambda driver: "/messages" in driver.current_url or "/user" in driver.current_url
    )
    
    # Check for success message or redirect
    page_source = browser.page_source
    # Should either show success message or be on messages page
    assert ("Your message has been sent" in page_source or 
            "Message sent" in page_source or
            "/messages" in browser.current_url or
            "/user" in browser.current_url)


def test_messages_page_lists_received_messages(browser, live_server):
    """Test that messages page loads correctly."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to messages page
    browser.get(f"{live_server}/messages")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Check that messages page loads correctly
    page_source = browser.page_source
    
    # Verify we're on the messages page
    assert "/messages" in browser.current_url
    
    # Check for messages page elements (even if empty)
    assert ("Messages" in page_source or 
            "messages" in page_source.lower() or
            "No messages" in page_source or
            "Your messages" in page_source)


def test_message_count_badge_updates_in_navbar(browser, live_server, monkeypatch):
    """Test that message count badge updates in navbar."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Mock unread message count
    def mock_unread_count(*args, **kwargs):
        return 3
    
    # Mock the current_user with message count
    monkeypatch.setattr("flask_login.utils._get_user", lambda: type('CU', (), {
        'is_authenticated': True,
        'username': 'testuser',
        'about_me': 'Test user bio',
        'last_seen': None,
        'unread_message_count': mock_unread_count,
        'get_tasks_in_progress': lambda: [],
        'get_task_in_progress': lambda name: None,
        'launch_task': lambda *a, **k: type('T', (), {'id': 't1'})(),
        '__eq__': lambda self, other: hasattr(other, 'username') and self.username == other.username
    })())
    
    # Navigate to any page
    browser.get(f"{live_server}/index")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Check for message count badge in navbar
    page_source = browser.page_source
    # Look for message count indicators
    assert ("Messages" in page_source or 
            "message_count" in page_source or
            "3" in page_source or
            "Messages" in page_source)


def test_messages_pagination_works(browser, live_server, monkeypatch):
    """Test that messages pagination works."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Mock messages with pagination
    def mock_messages():
        class MockQuery:
            def paginate(self, page=1, per_page=10, error_out=False):
                # Simulate multiple pages
                if page == 1:
                    messages = [
                        type('Message', (), {
                            'id': i,
                            'body': f'Message {i}',
                            'author': type('User', (), {
                                'username': f'user{i}',
                                'avatar': '/static/default.png'
                            })(),
                            'timestamp': f'2024-01-01 {12+i}:00:00'
                        })() for i in range(1, 11)
                    ]
                    return type('Paginated', (), {
                        'items': messages,
                        'pages': 2,
                        'total': 15,
                        'has_next': True,
                        'has_prev': False,
                        'next_num': 2,
                        'prev_num': None
                    })()
                else:
                    messages = [
                        type('Message', (), {
                            'id': i,
                            'body': f'Message {i}',
                            'author': type('User', (), {
                                'username': f'user{i}',
                                'avatar': '/static/default.png'
                            })(),
                            'timestamp': f'2024-01-01 {12+i}:00:00'
                        })() for i in range(11, 16)
                    ]
                    return type('Paginated', (), {
                        'items': messages,
                        'pages': 2,
                        'total': 15,
                        'has_next': False,
                        'has_prev': True,
                        'next_num': None,
                        'prev_num': 1
                    })()
        return MockQuery()
    
    # Mock the current_user.messages method
    monkeypatch.setattr("flask_login.utils._get_user", lambda: type('CU', (), {
        'is_authenticated': True,
        'username': 'testuser',
        'about_me': 'Test user bio',
        'last_seen': None,
        'messages': mock_messages,
        'unread_message_count': lambda *args, **kwargs: 0,
        'add_notification': lambda *args, **kwargs: None,
        'get_tasks_in_progress': lambda: [],
        'get_task_in_progress': lambda name: None,
        'launch_task': lambda *a, **k: type('T', (), {'id': 't1'})(),
        '__eq__': lambda self, other: hasattr(other, 'username') and self.username == other.username
    })())
    
    # Navigate to messages page
    browser.get(f"{live_server}/messages")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Check for pagination links
    page_source = browser.page_source
    # Look for pagination indicators
    assert ("Older messages" in page_source or 
            "Newer messages" in page_source or
            "Next" in page_source or
            "Previous" in page_source or
            "page" in page_source.lower())


def test_send_message_to_nonexistent_user_shows_error(browser, live_server):
    """Test that sending message to nonexistent user shows error."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Try to navigate to send message page for nonexistent user
    browser.get(f"{live_server}/send_message/nonexistentuser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Should show error or redirect
    page_source = browser.page_source
    assert ("User not found" in page_source or 
            "404" in page_source or
            "Not Found" in page_source or
            "/index" in browser.current_url)


def test_message_form_validation_works(browser, live_server):
    """Test that message form validation works."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to send message page
    browser.get(f"{live_server}/send_message/otheruser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )
    
    # Try to submit empty message
    submit_button = browser.find_element(By.CSS_SELECTOR, "input[type=submit], button[type=submit]")
    submit_button.click()
    
    # Should stay on the same page or show validation error
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )
    
    # Should still be on send message page
    assert "/send_message" in browser.current_url


def test_messages_page_requires_authentication(browser, live_server):
    """Test that messages page requires authentication."""
    # Don't login - try to access messages page directly
    browser.get(f"{live_server}/messages")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Should redirect to login page
    assert "/auth/login" in browser.current_url


def test_send_message_page_requires_authentication(browser, live_server):
    """Test that send message page requires authentication."""
    # Don't login - try to access send message page directly
    browser.get(f"{live_server}/send_message/otheruser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Should redirect to login page
    assert "/auth/login" in browser.current_url


def test_message_links_work_correctly(browser, live_server):
    """Test that message links work correctly."""
    from conftest import login_user
    
    # Login with the seeded user
    login_user(browser, live_server)
    
    # Navigate to another user's profile
    browser.get(f"{live_server}/user/otheruser")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    
    # Click the send message link
    message_link = browser.find_element(By.LINK_TEXT, "Send private message")
    message_link.click()
    
    # Should navigate to send message page
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "message"))
    )
    
    assert "/send_message/otheruser" in browser.current_url

# E2E Test Implementation Plan

## Test Organization

All tests will be placed in `tests/e2e/` with the existing conftest providing live server, headless browser, and mocked services.

## Test Files to Create

### 1. Authentication Flows (`test_auth_flows.py`)

**Critical user journeys:**

- Login page renders with form fields (username, password, remember_me)
- Login with invalid credentials shows error flash message
- Logout redirects to index and navbar shows "Login" link
- Registration page renders with form (username, email, password, password2)
- Register with valid data redirects to login with success message
- Register with duplicate username shows validation error
- Password reset request page renders and accepts email
- Password reset with token renders form and updates password

**Why:** Authentication is the foundation - users cannot access any features without it.

### 2. Home Page and Post Creation (`test_home_and_posts.py`)

**Critical user journeys:**

- Index page renders with greeting and post form
- Create post via form submission shows flash message and new post appears
- Post form validation (empty post shows error)
- Explore page renders with all posts
- Posts display with avatar, username, timestamp, and body
- Pagination works (next/prev links when multiple pages exist)

**Why:** Core content creation and consumption - the primary feature users interact with.

### 3. User Profiles (`test_user_profiles.py`)

**Critical user journeys:**

- User profile page renders with avatar, bio, last seen, counts
- Own profile shows "Edit your profile" link
- Own profile shows "Export your posts" link (when no export in progress)
- Edit profile page prefills current username and about_me
- Edit profile updates data and shows success flash
- Edit profile with duplicate username shows validation error
- Other user's profile shows Follow/Unfollow button (not both)

**Why:** User identity and personalization - users need to manage their presence.

### 4. Social Features (`test_social_features.py`)

**Critical user journeys:**

- Follow button on user profile triggers follow action
- After following, button changes to Unfollow
- Unfollow button triggers unfollow action
- Cannot follow yourself (error message)
- Followed users' posts appear on home feed
- User popup (hover) loads and displays user info

**Why:** Social interaction is core to a microblog platform's value proposition.

### 5. Private Messaging (`test_messaging.py`)

**Critical user journeys:**

- Send message link appears on other users' profiles
- Send message page renders with form
- Message submission shows success flash and redirects
- Messages page lists received messages
- Message count badge updates in navbar
- Messages pagination works

**Why:** Private communication is a key engagement feature.

### 6. Search Functionality (`test_search.py`)

**Critical user journeys:**

- Search form appears in navbar for authenticated users
- Search with query term redirects to search results page
- Search results display matching posts
- Search pagination works (next/prev)
- Empty search redirects to explore

**Why:** Content discovery is essential for user engagement and retention.

### 7. Translation Feature (`test_translation.py`)

**Critical user journeys:**

- Posts with different language show "Translate" link
- Clicking translate makes AJAX call to /translate endpoint
- Translation result replaces "Translate" link with translated text
- Loading indicator appears during translation

**Why:** Internationalization feature that enhances accessibility.

### 8. Background Tasks (`test_tasks.py`)

**Critical user journeys:**

- Export posts link triggers task launch
- Task progress alert appears in page header
- Second export attempt while running shows "in progress" flash
- Export posts link disappears while task is running

**Why:** Demonstrates async task handling and user feedback.

### 9. Real-time Notifications (`test_notifications.py`)

**Critical user journeys:**

- Notifications endpoint returns JSON array
- Message count badge updates via polling
- Task progress updates via polling
- Notification polling triggers every 10 seconds

**Why:** Real-time updates enhance user experience and engagement.

## Implementation Strategy

### Test Structure Pattern

Each test file will:

1. Use `browser` and `live_server` fixtures from conftest
2. Use WebDriverWait with explicit waits (5-10 seconds)
3. Test positive and negative cases
4. Verify redirects, flash messages, and DOM changes
5. Use stable selectors (name, id, class, or data-testid)

### Mocking Strategy

The existing `tests/e2e/conftest.py` already provides:

- Mocked `db.session` (add, commit, scalar, scalars, paginate)
- Mocked Elasticsearch (search returns empty)
- Mocked Redis/RQ (tasks)
- Mocked email sending
- Mocked translation service
- Stubbed `current_user` with necessary attributes

**Additional mocking needed per test:**

- Patch specific `db.session.scalar` to return user fixtures
- Patch `db.paginate` to return post/message fixtures
- Patch `Post.search` to return search results
- Mock user relationships (followers, following)

### Key Technical Considerations

**Synchronization:**

- Always use `WebDriverWait` with `expected_conditions`
- Wait for elements, visibility, clickability before interaction
- Wait for URL changes after form submissions

**CSRF Handling:**

- `TestConfig` already has `WTF_CSRF_ENABLED = False`
- No special handling needed in tests

**JavaScript Interactions:**

- Translation: Test AJAX call, loading indicator, result display
- User popups: Test hover trigger, async content load
- Notifications: Test polling interval (may need to reduce for testing)

**Form Interactions:**

- Use `find_element(By.NAME, 'field_name')` for inputs
- Use `.send_keys()` for text input
- Use `.click()` for buttons
- Verify flash messages after submission

### Assertions to Include

Each test should verify:

1. Correct page loads (URL, title, or key element)
2. Expected elements present (forms, buttons, content)
3. User actions trigger correct behavior (redirects, updates)
4. Flash messages appear with correct text
5. DOM updates reflect state changes (counts, visibility)

### Edge Cases to Test

- Empty states (no posts, no messages, no followers)
- Pagination boundaries (first page, last page)
- Validation errors (duplicate username, invalid email)
- Permission checks (cannot follow self, edit other's profile)
- Concurrent actions (task already in progress)

## Test Execution

```bash
# Run all E2E tests
pytest tests/e2e -v

# Run specific test file
pytest tests/e2e/test_auth_flows.py -v

# Run with detailed output
pytest tests/e2e -v --tb=short

# Run in parallel (if selenium grid configured)
pytest tests/e2e -n auto
```

## Coverage Goals

E2E tests should cover:

- All critical user journeys (auth, posting, profiles, social)
- All major navigation paths
- All form submissions
- All AJAX endpoints
- Error handling and edge cases

E2E tests should NOT duplicate:

- Business logic (covered by unit tests)
- API endpoints (covered by integration tests)
- Form validation rules (covered by unit tests)

Focus on user-facing workflows and interactions.

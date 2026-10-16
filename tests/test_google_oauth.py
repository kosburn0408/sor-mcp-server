"""Tests for Google sign-in and the Classroom export (Google is mocked)."""

from __future__ import annotations

import base64
import hashlib
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from src.client import google_oauth
from src.client.google_classroom import CLASSROOM_API_BASE
from webapp import app

BASE = "/api/v1/google-classroom"


@pytest.fixture(autouse=True)
def configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "cid.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "shh")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "https://sor.example.org/api/v1/google-classroom/oauth/callback")
    google_oauth.store.clear()
    yield
    google_oauth.store.clear()


def new_client() -> TestClient:
    return TestClient(app, base_url="https://sor.example.org", follow_redirects=False)


def start(client: TestClient) -> tuple[str, dict]:
    r = client.get(f"{BASE}/oauth/start")
    assert r.status_code == 302
    url = urlparse(r.headers["location"])
    return r.headers["location"], parse_qs(url.query)


GOOD_TOKEN = {
    "access_token": "ya29.token",
    "expires_in": 3599,
    "scope": " ".join(google_oauth.SCOPES),
}


def test_start_sends_the_right_request_to_google() -> None:
    client = new_client()
    location, q = start(client)
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert q["client_id"] == ["cid.apps.googleusercontent.com"]
    assert q["response_type"] == ["code"]
    assert q["access_type"] == ["online"]
    assert q["code_challenge_method"] == ["S256"]
    assert set(q["scope"][0].split()) == set(google_oauth.SCOPES)
    # Only narrow scopes: nothing about rosters, grades or student work.
    assert "rosters" not in q["scope"][0] and "student-submissions" not in q["scope"][0]
    assert "HttpOnly" in client.get(f"{BASE}/oauth/start").headers["set-cookie"]


def test_not_configured_gives_demo_mode_and_a_clear_message(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID")
    client = new_client()
    assert client.get(f"{BASE}/oauth/status").json()["configured"] is False
    r = client.get(f"{BASE}/oauth/start")
    assert r.status_code == 503 and "not set up" in r.json()["detail"]
    assert client.get(f"{BASE}/courses").json()["demo_mode"] is True


@respx.mock
def test_full_sign_in_then_courses_and_publish() -> None:
    client = new_client()
    _, q = start(client)
    state = q["state"][0]
    token_route = respx.post(google_oauth.TOKEN_URL).mock(return_value=httpx.Response(200, json=GOOD_TOKEN))
    courses = respx.get(f"{CLASSROOM_API_BASE}/courses").mock(
        return_value=httpx.Response(200, json={"courses": [{"id": "123", "name": "Room 4"}]})
    )
    work = respx.post(f"{CLASSROOM_API_BASE}/courses/123/courseWork").mock(
        return_value=httpx.Response(200, json={"id": "w1", "alternateLink": "https://classroom.google.com/c/123/a/w1"})
    )

    cb = client.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": state})
    assert cb.status_code == 302 and cb.headers["location"] == "/?classroom=connected"

    # The code exchange used PKCE and the secret, server side.
    sent = parse_qs(token_route.calls.last.request.content.decode())
    assert sent["code"] == ["abc"] and sent["client_secret"] == ["shh"]
    verifier = sent["code_verifier"][0]
    challenge = q["code_challenge"][0]
    assert base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode() == challenge

    assert client.get(f"{BASE}/oauth/status").json()["connected"] is True
    got = client.get(f"{BASE}/courses").json()
    assert got["demo_mode"] is False and got["courses"][0]["id"] == "123"
    assert courses.calls.last.request.headers["authorization"] == "Bearer ya29.token"

    pub = client.post(f"{BASE}/publish", json={"course_id": "123", "title": "T", "description": "cat sat"})
    assert pub.json()["status"] == "published" and pub.json()["demo_mode"] is False
    assert work.called


def test_browser_never_receives_the_access_token() -> None:
    with respx.mock:
        client = new_client()
        _, q = start(client)
        respx.post(google_oauth.TOKEN_URL).mock(return_value=httpx.Response(200, json=GOOD_TOKEN))
        cb = client.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": q["state"][0]})
    cookies = " ".join(cb.headers.get_list("set-cookie"))
    assert "ya29" not in cookies and "ya29" not in cb.text
    assert "HttpOnly" in cookies and "Secure" in cookies and "SameSite=lax" in cookies


@respx.mock
def test_state_must_match_this_browser_and_be_single_use() -> None:
    victim, attacker = new_client(), new_client()
    _, q = start(attacker)  # attacker begins a sign-in...
    respx.post(google_oauth.TOKEN_URL).mock(return_value=httpx.Response(200, json=GOOD_TOKEN))
    # ...and tricks the victim's browser into finishing it: no matching state cookie.
    r = victim.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": q["state"][0]})
    assert r.headers["location"] == "/?classroom=error"
    assert victim.get(f"{BASE}/oauth/status").json()["connected"] is False
    # The state was consumed, so replaying it in the right browser also fails.
    r2 = attacker.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": q["state"][0]})
    assert r2.headers["location"] == "/?classroom=error"


def test_unknown_state_and_denied_consent() -> None:
    client = new_client()
    assert client.get(f"{BASE}/oauth/callback", params={"code": "x", "state": "nope"}).headers["location"] == "/?classroom=error"
    _, q = start(client)
    r = client.get(f"{BASE}/oauth/callback", params={"error": "access_denied", "state": q["state"][0]})
    assert r.headers["location"] == "/?classroom=cancelled"


@respx.mock
def test_missing_permissions_are_rejected() -> None:
    client = new_client()
    _, q = start(client)
    partial = dict(GOOD_TOKEN, scope=google_oauth.SCOPES[0])
    respx.post(google_oauth.TOKEN_URL).mock(return_value=httpx.Response(200, json=partial))
    r = client.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": q["state"][0]})
    assert r.headers["location"] == "/?classroom=error"
    assert client.get(f"{BASE}/oauth/status").json()["connected"] is False


@respx.mock
def test_google_rejecting_the_token_tells_the_teacher_to_reconnect() -> None:
    client = new_client()
    _, q = start(client)
    respx.post(google_oauth.TOKEN_URL).mock(return_value=httpx.Response(200, json=GOOD_TOKEN))
    client.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": q["state"][0]})
    respx.get(f"{CLASSROOM_API_BASE}/courses").mock(return_value=httpx.Response(401, json={}))
    r = client.get(f"{BASE}/courses")
    assert r.status_code == 401 and "connect Google Classroom again" in r.json()["detail"]


@respx.mock
def test_logout_revokes_and_forgets() -> None:
    client = new_client()
    _, q = start(client)
    respx.post(google_oauth.TOKEN_URL).mock(return_value=httpx.Response(200, json=GOOD_TOKEN))
    client.get(f"{BASE}/oauth/callback", params={"code": "abc", "state": q["state"][0]})
    revoke = respx.post(google_oauth.REVOKE_URL).mock(return_value=httpx.Response(200))
    assert client.post(f"{BASE}/oauth/logout").json()["status"] == "disconnected"
    assert revoke.called and revoke.calls.last.request.url.params["token"] == "ya29.token"
    assert client.get(f"{BASE}/oauth/status").json()["connected"] is False
    assert client.get(f"{BASE}/courses").json()["demo_mode"] is True


def test_sessions_expire(monkeypatch) -> None:
    sid = google_oauth.store.create_session("tok", 3599)
    assert google_oauth.store.get_token(sid) == "tok"
    real = google_oauth.time.time
    monkeypatch.setattr(google_oauth.time, "time", lambda: real() + 4000)
    assert google_oauth.store.get_token(sid) is None


def test_no_demo_results_when_a_real_token_is_given() -> None:
    with respx.mock:
        respx.get(f"{CLASSROOM_API_BASE}/courses").mock(return_value=httpx.Response(200, json={"courses": []}))
        r = new_client().get(f"{BASE}/courses", headers={"Authorization": "Bearer abc"})
    assert r.json()["demo_mode"] is False

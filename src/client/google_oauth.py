"""Google OAuth 2.0 (authorization code + PKCE) for the Google Classroom export.

Design choices, chosen to fit the app's "no student data kept" promise:
  - Only two narrow scopes are requested: list the teacher's own courses and create
    assignments. No roster, grade or student-work scopes.
  - Access is online only (no refresh token). The access token lives in server memory for
    its lifetime (about an hour) and is never written to disk or logs.
  - The browser only ever holds a random session id in an HttpOnly cookie, not the token.

Setup (Google Cloud Console, once per deployment) is described in USER_GUIDE.md.

Environment:
  GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REDIRECT_URI
  (the redirect URI must exactly match one registered in the console, and ends with
  /api/v1/google-classroom/oauth/callback).
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"

SCOPES = (
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
)

PENDING_TTL_SECONDS = 10 * 60
MAX_PENDING = 500
MAX_SESSIONS = 5000


class OAuthError(Exception):
    """Sign-in with Google failed; the message is safe to show to a teacher."""


@dataclass(frozen=True)
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str

    @property
    def secure_cookies(self) -> bool:
        return self.redirect_uri.lower().startswith("https://")

    @classmethod
    def from_env(cls) -> "OAuthConfig | None":
        cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
        redirect = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
        if not (cid and secret and redirect):
            return None
        return cls(cid, secret, redirect)


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_auth_url(config: OAuthConfig, state: str, code_challenge: str) -> str:
    params = {
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


class SessionStore:
    """Short-lived, in-memory store. Nothing here survives a restart, by design."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: dict[str, tuple[float, str]] = {}  # state -> (expires, code_verifier)
        self._sessions: dict[str, tuple[float, str]] = {}  # session id -> (expires, access token)

    def _purge(self, now: float) -> None:
        for table in (self._pending, self._sessions):
            for key in [k for k, (exp, _) in table.items() if exp <= now]:
                del table[key]

    def start(self, verifier: str) -> str:
        state = secrets.token_urlsafe(32)
        now = time.time()
        with self._lock:
            self._purge(now)
            if len(self._pending) >= MAX_PENDING:
                oldest = min(self._pending, key=lambda k: self._pending[k][0])
                del self._pending[oldest]
            self._pending[state] = (now + PENDING_TTL_SECONDS, verifier)
        return state

    def finish(self, state: str) -> str | None:
        """Consume a pending sign-in and return its PKCE verifier (single use)."""
        with self._lock:
            self._purge(time.time())
            entry = self._pending.pop(state, None)
        return entry[1] if entry else None

    def create_session(self, access_token: str, expires_in: int) -> str:
        sid = secrets.token_urlsafe(32)
        now = time.time()
        lifetime = max(60, min(int(expires_in), 3600))
        with self._lock:
            self._purge(now)
            if len(self._sessions) >= MAX_SESSIONS:
                oldest = min(self._sessions, key=lambda k: self._sessions[k][0])
                del self._sessions[oldest]
            self._sessions[sid] = (now + lifetime, access_token)
        return sid

    def get_token(self, sid: str | None) -> str | None:
        if not sid:
            return None
        with self._lock:
            self._purge(time.time())
            entry = self._sessions.get(sid)
        return entry[1] if entry else None

    def lifetime_left(self, sid: str | None) -> int:
        if not sid:
            return 0
        with self._lock:
            entry = self._sessions.get(sid)
        return max(0, int(entry[0] - time.time())) if entry else 0

    def delete(self, sid: str | None) -> str | None:
        """Remove a session and return its token (so the caller can revoke it)."""
        if not sid:
            return None
        with self._lock:
            entry = self._sessions.pop(sid, None)
        return entry[1] if entry else None

    def clear(self) -> None:
        with self._lock:
            self._pending.clear()
            self._sessions.clear()


store = SessionStore()


def exchange_code(config: OAuthConfig, code: str, verifier: str, client: httpx.Client | None = None) -> dict[str, Any]:
    """Trade the one-time code for an access token. Raises OAuthError with a safe message."""
    owns = client is None
    http = client or httpx.Client(timeout=10.0)
    try:
        response = http.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "redirect_uri": config.redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            },
        )
    except httpx.HTTPError:
        raise OAuthError("Could not reach Google to finish signing in. Please try again.") from None
    finally:
        if owns:
            http.close()
    if response.status_code != 200:
        raise OAuthError("Google did not accept the sign-in. Please try connecting again.")
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise OAuthError("Google did not return an access token.")
    granted = set(str(data.get("scope", "")).split())
    if not set(SCOPES) <= granted:
        raise OAuthError(
            "Not all of the requested Classroom permissions were granted. "
            "Please connect again and allow both permissions."
        )
    return {"access_token": token, "expires_in": int(data.get("expires_in", 3600))}


def revoke(token: str, client: httpx.Client | None = None) -> None:
    """Best-effort revoke at Google. Failures are ignored; the session is deleted anyway."""
    owns = client is None
    http = client or httpx.Client(timeout=5.0)
    try:
        http.post(REVOKE_URL, params={"token": token})
    except httpx.HTTPError:
        pass
    finally:
        if owns:
            http.close()

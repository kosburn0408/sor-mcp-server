"""FastAPI router for Google Classroom coursework export.

Without Google credentials configured, or without a signed-in teacher, the export runs in
demo mode (nothing is sent to Google). With them, teachers sign in with Google (OAuth 2.0
authorization code + PKCE) and assignments are created in their own Classroom.

Endpoints (all under /api/v1/google-classroom):
  GET  /oauth/status    whether sign-in is set up and whether this browser is connected
  GET  /oauth/start     begin Google sign-in (redirects to Google)
  GET  /oauth/callback  Google redirects back here
  POST /oauth/logout    disconnect and revoke
  GET  /courses         the teacher's active courses
  POST /publish         create the assignment
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Cookie, Header, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel

from src.client import google_oauth
from src.client.google_classroom import ClassroomAPIError, list_courses, publish_coursework
from src.client.google_oauth import OAuthConfig, OAuthError

router = APIRouter(prefix="/api/v1/google-classroom", tags=["Google Classroom"])

SESSION_COOKIE = "sor_gc_session"
STATE_COOKIE = "sor_gc_state"


class CourseworkPublishRequest(BaseModel):
    course_id: str
    title: str
    description: str
    points: float = 100.0
    due_date: dict[str, int] | None = None
    access_token: str | None = None


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split("Bearer ", 1)[1]
    return None


def _cookie_args(config: OAuthConfig, max_age: int) -> dict[str, Any]:
    return {"httponly": True, "samesite": "lax", "secure": config.secure_cookies, "max_age": max_age, "path": "/"}


@router.get("/oauth/status")
async def oauth_status(sor_gc_session: str | None = Cookie(None)) -> dict[str, Any]:
    config = OAuthConfig.from_env()
    connected = google_oauth.store.get_token(sor_gc_session) is not None
    return {
        "configured": config is not None,
        "connected": connected,
        "seconds_left": google_oauth.store.lifetime_left(sor_gc_session) if connected else 0,
        "demo_mode": not connected,
        "permissions": [s.rsplit("/", 1)[-1] for s in google_oauth.SCOPES],
    }


@router.get("/oauth/start")
async def oauth_start() -> Response:
    config = OAuthConfig.from_env()
    if config is None:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not set up on this server. Exports run in demo mode.",
        )
    verifier, challenge = google_oauth.pkce_pair()
    state = google_oauth.store.start(verifier)
    response = RedirectResponse(google_oauth.build_auth_url(config, state, challenge), status_code=302)
    response.set_cookie(STATE_COOKIE, state, **_cookie_args(config, google_oauth.PENDING_TTL_SECONDS))
    return response


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    sor_gc_state: str | None = Cookie(None),
) -> Response:
    config = OAuthConfig.from_env()
    if config is None:
        raise HTTPException(status_code=503, detail="Google sign-in is not set up on this server.")

    def back(flag: str) -> Response:
        resp = RedirectResponse(f"/?classroom={flag}", status_code=302)
        resp.delete_cookie(STATE_COOKIE, path="/")
        return resp

    if error or not code or not state:
        if state:
            google_oauth.store.finish(state)
        return back("cancelled" if error == "access_denied" else "error")
    verifier = google_oauth.store.finish(state)
    # The state must come back unchanged, and must belong to this browser (stops a
    # sign-in started by someone else from being completed here).
    if verifier is None or sor_gc_state != state:
        return back("error")
    try:
        token = google_oauth.exchange_code(config, code, verifier)
    except OAuthError:
        return back("error")
    sid = google_oauth.store.create_session(token["access_token"], token["expires_in"])
    resp = back("connected")
    resp.set_cookie(SESSION_COOKIE, sid, **_cookie_args(config, min(token["expires_in"], 3600)))
    return resp


@router.post("/oauth/logout")
async def oauth_logout(sor_gc_session: str | None = Cookie(None)) -> Response:
    token = google_oauth.store.delete(sor_gc_session)
    if token:
        google_oauth.revoke(token)
    response = Response(content='{"status":"disconnected"}', media_type="application/json")
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


def _resolve_token(header_token: str | None, body_token: str | None, session_id: str | None) -> str | None:
    return header_token or body_token or google_oauth.store.get_token(session_id)


def _friendly(status: int) -> str:
    if status in (401, 403):
        return "Google Classroom did not accept the connection. Please connect Google Classroom again."
    return f"Google Classroom could not be reached (error {status}). Please try again."


@router.get("/courses")
async def get_courses_route(
    authorization: str | None = Header(None),
    token: str | None = None,
    sor_gc_session: str | None = Cookie(None),
) -> dict[str, Any]:
    """Fetch active Google Classroom courses where the user is a teacher."""
    access_token = _resolve_token(_bearer(authorization), token, sor_gc_session)

    if not access_token:
        # Demo mode: nothing is sent to Google.
        return {
            "status": "ok",
            "courses": [
                {"id": "demo_course_101", "name": "1st Grade Reading — Unit 3", "section": "Period 1"},
                {"id": "demo_course_102", "name": "MTSS Literacy Support", "section": "Small Group"},
            ],
            "demo_mode": True,
        }

    try:
        courses = await list_courses(access_token)
    except ClassroomAPIError as exc:
        raise HTTPException(status_code=401 if exc.status in (401, 403) else 502, detail=_friendly(exc.status)) from None
    return {"status": "ok", "courses": courses, "demo_mode": False}


@router.post("/publish")
async def publish_coursework_route(
    req: CourseworkPublishRequest,
    authorization: str | None = Header(None),
    sor_gc_session: str | None = Cookie(None),
) -> dict[str, Any]:
    """Publish a decodable text assignment to Google Classroom."""
    access_token = _resolve_token(_bearer(authorization), req.access_token or None, sor_gc_session)

    if not access_token or access_token.startswith("demo_"):
        # Demo response: nothing is sent to Google.
        return {
            "status": "published",
            "coursework_id": "cw_demo_98765",
            "alternateLink": f"https://classroom.google.com/c/{req.course_id}/a/demo_98765/details",
            "title": req.title,
            "demo_mode": True,
        }

    result = await publish_coursework(
        access_token=access_token,
        course_id=req.course_id,
        title=req.title,
        description=req.description,
        points=req.points,
        due_date=req.due_date,
    )

    if result.get("error"):
        status = result.get("status_code", 400)
        raise HTTPException(
            status_code=401 if status in (401, 403) else 400,
            detail=_friendly(status) if status in (401, 403) else "Google Classroom could not create the assignment.",
        )

    return {"status": "published", "coursework": result, "alternateLink": result.get("alternateLink"), "demo_mode": False}

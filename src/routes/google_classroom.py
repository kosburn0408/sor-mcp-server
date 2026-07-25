"""FastAPI router for Google Classroom OAuth coursework integration.

Exposes REST endpoints:
  - GET /api/v1/google-classroom/courses
  - POST /api/v1/google-classroom/publish
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from src.client.google_classroom import list_courses, publish_coursework

router = APIRouter(prefix="/api/v1/google-classroom", tags=["Google Classroom"])


class CourseworkPublishRequest(BaseModel):
    course_id: str
    title: str
    description: str
    points: float = 100.0
    due_date: dict[str, int] | None = None
    access_token: str | None = None


@router.get("/courses")
async def get_courses_route(authorization: str | None = Header(None), token: str | None = None) -> dict[str, Any]:
    """Fetch active Google Classroom courses where user is a teacher."""
    access_token = token
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.split("Bearer ", 1)[1]

    if not access_token:
        # Mock/Demo fallback for testing without live OAuth
        return {
            "status": "ok",
            "courses": [
                {"id": "demo_course_101", "name": "1st Grade Reading — Unit 3", "section": "Period 1"},
                {"id": "demo_course_102", "name": "MTSS Literacy Support", "section": "Small Group"},
            ],
            "demo_mode": True,
        }

    courses = await list_courses(access_token)
    return {"status": "ok", "courses": courses, "demo_mode": False}


@router.post("/publish")
async def publish_coursework_route(
    req: CourseworkPublishRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Publish decodable text assignment to Google Classroom."""
    access_token = req.access_token
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.split("Bearer ", 1)[1]

    if not access_token or access_token.startswith("demo_"):
        # Demo response for local testing
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
        raise HTTPException(status_code=400, detail=result.get("detail", "Failed to publish to Google Classroom"))

    return {"status": "published", "coursework": result, "alternateLink": result.get("alternateLink")}

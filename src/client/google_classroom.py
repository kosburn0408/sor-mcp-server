"""Google Classroom API client module.

Provides OAuth2 integration with Google Classroom REST API v1 for listing teacher
courses and publishing structured literacy assignments/coursework.
"""
from __future__ import annotations

from typing import Any
import httpx

CLASSROOM_API_BASE = "https://classroom.googleapis.com/v1"


async def list_courses(access_token: str) -> list[dict[str, Any]]:
    """List active Google Classroom courses where the user is a teacher.

    Args:
        access_token: Valid OAuth2 access token for Google Classroom.

    Returns:
        List of course dictionaries containing id, name, section, description.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{CLASSROOM_API_BASE}/courses",
            headers=headers,
            params={"teacherId": "me", "courseStates": "ACTIVE"},
        )

        if response.status_code != 200:
            return []

        data = response.json()
        return data.get("courses", [])


async def publish_coursework(
    access_token: str,
    course_id: str,
    title: str,
    description: str,
    points: float = 100.0,
    due_date: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Publish a new coursework assignment to a Google Classroom course.

    Args:
        access_token: Valid OAuth2 access token for Google Classroom.
        course_id: Google Classroom course ID.
        title: Title of the assignment.
        description: Instructions or body of the decodable text / routine.
        points: Maximum points for the coursework.
        due_date: Optional dict with 'year', 'month', 'day'.

    Returns:
        Created coursework object from Google Classroom API.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "title": title,
        "description": description,
        "maxPoints": points,
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED",
    }

    if due_date and isinstance(due_date, dict):
        payload["dueDate"] = {
            "year": due_date.get("year", 2026),
            "month": due_date.get("month", 1),
            "day": due_date.get("day", 1),
        }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{CLASSROOM_API_BASE}/courses/{course_id}/courseWork",
            headers=headers,
            json=payload,
        )

        if response.status_code in (200, 201):
            return response.json()

        return {
            "error": True,
            "status_code": response.status_code,
            "detail": response.text,
        }

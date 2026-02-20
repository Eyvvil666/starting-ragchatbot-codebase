"""Tests for FastAPI API endpoints.

Uses an inline test app to avoid importing the real app.py, which mounts
static files from ../frontend (a directory that doesn't exist in CI/test
environments).
"""
import sys
import os
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Pydantic models (mirror app.py)
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


# ---------------------------------------------------------------------------
# Inline test app factory
# ---------------------------------------------------------------------------

def _build_test_app(rag) -> FastAPI:
    """Return a minimal FastAPI app that mirrors the real /api/* endpoints."""
    app = FastAPI()

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag.session_manager.create_session()
            answer, sources = rag.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/session/{session_id}")
    async def delete_session(session_id: str):
        rag.session_manager.clear_session(session_id)
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return JSONResponse({"status": "ok"})

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_rag_system):
    """TestClient backed by the inline test app with a mocked RAGSystem."""
    app = _build_test_app(mock_rag_system)
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------

class TestQueryEndpoint:
    def test_query_happy_path_with_session(self, client, mock_rag_system):
        resp = client.post(
            "/api/query",
            json={"query": "What is Python?", "session_id": "sess-1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "Test answer"
        assert data["sources"] == ["source1"]
        assert data["session_id"] == "sess-1"

    def test_query_auto_generates_session_when_omitted(self, client, mock_rag_system):
        resp = client.post("/api/query", json={"query": "Hello"})
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "generated-session-id"
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_query_explicit_none_session_also_generates(self, client, mock_rag_system):
        resp = client.post("/api/query", json={"query": "Hi", "session_id": None})
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "generated-session-id"

    def test_query_calls_rag_with_correct_arguments(self, client, mock_rag_system):
        client.post("/api/query", json={"query": "Teach me Python", "session_id": "s1"})
        mock_rag_system.query.assert_called_once_with("Teach me Python", "s1")

    def test_query_missing_query_field_returns_422(self, client):
        resp = client.post("/api/query", json={})
        assert resp.status_code == 422

    def test_query_empty_string_is_accepted(self, client):
        resp = client.post("/api/query", json={"query": ""})
        assert resp.status_code == 200

    def test_query_rag_exception_returns_500(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("DB failure")
        resp = client.post("/api/query", json={"query": "x", "session_id": "s1"})
        assert resp.status_code == 500
        assert "DB failure" in resp.json()["detail"]

    def test_query_response_contains_all_fields(self, client):
        resp = client.post("/api/query", json={"query": "test", "session_id": "s1"})
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

    def test_query_sources_is_a_list(self, client):
        resp = client.post("/api/query", json={"query": "test", "session_id": "s1"})
        assert isinstance(resp.json()["sources"], list)

    def test_query_empty_sources_list_is_valid(self, client, mock_rag_system):
        mock_rag_system.query.return_value = ("No sources answer", [])
        resp = client.post("/api/query", json={"query": "test", "session_id": "s1"})
        assert resp.status_code == 200
        assert resp.json()["sources"] == []


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------

class TestCoursesEndpoint:
    def test_courses_returns_200(self, client):
        resp = client.get("/api/courses")
        assert resp.status_code == 200

    def test_courses_total_count(self, client):
        assert client.get("/api/courses").json()["total_courses"] == 2

    def test_courses_title_list(self, client):
        assert client.get("/api/courses").json()["course_titles"] == ["Course A", "Course B"]

    def test_courses_response_shape(self, client):
        data = client.get("/api/courses").json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

    def test_courses_zero_courses(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }
        data = client.get("/api/courses").json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_courses_analytics_error_returns_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = RuntimeError("Analytics error")
        resp = client.get("/api/courses")
        assert resp.status_code == 500
        assert "Analytics error" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /api/session/{session_id}
# ---------------------------------------------------------------------------

class TestSessionEndpoint:
    def test_delete_session_returns_ok(self, client):
        resp = client.delete("/api/session/my-session")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_delete_session_calls_clear(self, client, mock_rag_system):
        client.delete("/api/session/abc-123")
        mock_rag_system.session_manager.clear_session.assert_called_once_with("abc-123")


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    def test_root_returns_200(self, client):
        assert client.get("/").status_code == 200

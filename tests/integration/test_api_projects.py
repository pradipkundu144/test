from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_session_factory
from app.main import app


@pytest.fixture(autouse=True)
def _reset_tables(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        session.execute(text("TRUNCATE projects CASCADE"))
        session.commit()


@pytest.fixture
def client(session_factory: sessionmaker) -> Iterator[TestClient]:
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _valid_body() -> dict:
    return {
        "name": "API Project",
        "project_type": "NEW",
        "source": "PPM",
        "created_by": "api-tester",
        "description": "made via API",
        "source_reference_id": "PPM-API-1",
        "configuration": {
            "context": "api context",
            "goals": "api goals",
            "scope": "api scope",
            "constraints": "none",
            "tech_stack": {"backend": ["Python"], "db": ["PostgreSQL"]},
            "coding_standards": "PEP 8",
        },
    }


def test_health_returns_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_openapi_and_swagger_available(client: TestClient) -> None:
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_post_creates_project_and_returns_201(client: TestClient) -> None:
    r = client.post("/api/v1/projects", json=_valid_body())

    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "API Project"
    assert body["status"] == "DRAFT"
    assert body["project_type"] == "NEW"
    assert body["configuration"]["project_id"] == body["id"]
    assert body["configuration"]["tech_stack"] == {
        "backend": ["Python"],
        "db": ["PostgreSQL"],
    }


def test_post_rejects_invalid_project_type_with_422(client: TestClient) -> None:
    body = _valid_body()
    body["project_type"] = "UNKNOWN"

    r = client.post("/api/v1/projects", json=body)

    assert r.status_code == 422


def test_post_rejects_missing_configuration_with_422(client: TestClient) -> None:
    body = _valid_body()
    del body["configuration"]

    r = client.post("/api/v1/projects", json=body)

    assert r.status_code == 422


def test_get_returns_created_project(client: TestClient) -> None:
    created = client.post("/api/v1/projects", json=_valid_body()).json()

    r = client.get(f"/api/v1/projects/{created['id']}")

    assert r.status_code == 200
    assert r.json()["id"] == created["id"]
    assert r.json()["configuration"]["context"] == "api context"


def test_get_unknown_id_returns_404(client: TestClient) -> None:
    r = client.get(f"/api/v1/projects/{uuid4()}")

    assert r.status_code == 404
    assert r.json()["error"] == "project_not_found"


def test_patch_updates_project_fields_only(client: TestClient) -> None:
    created = client.post("/api/v1/projects", json=_valid_body()).json()

    r = client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"name": "Renamed Project", "status": "ACTIVE"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Renamed Project"
    assert body["status"] == "ACTIVE"
    # config untouched
    assert body["configuration"]["context"] == "api context"


def test_patch_updates_nested_configuration(client: TestClient) -> None:
    created = client.post("/api/v1/projects", json=_valid_body()).json()

    r = client.patch(
        f"/api/v1/projects/{created['id']}",
        json={
            "configuration": {
                "goals": "new goals",
                "tech_stack": {"backend": ["Rust"]},
            }
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "API Project"  # unchanged
    assert body["configuration"]["goals"] == "new goals"
    assert body["configuration"]["tech_stack"] == {"backend": ["Rust"]}
    assert body["configuration"]["context"] == "api context"  # unchanged


def test_patch_rejects_invalid_status(client: TestClient) -> None:
    created = client.post("/api/v1/projects", json=_valid_body()).json()

    r = client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"status": "COMPLETED"},
    )

    assert r.status_code == 422


def test_patch_unknown_id_returns_404(client: TestClient) -> None:
    r = client.patch(f"/api/v1/projects/{uuid4()}", json={"name": "x"})

    assert r.status_code == 404


def test_delete_removes_project_and_returns_204(
    client: TestClient,
    session_factory: sessionmaker,
) -> None:
    created = client.post("/api/v1/projects", json=_valid_body()).json()

    r = client.delete(f"/api/v1/projects/{created['id']}")

    assert r.status_code == 204
    assert r.content == b""

    with session_factory() as session:
        remaining = session.execute(
            text("SELECT COUNT(*) FROM projects WHERE id = :id"),
            {"id": created["id"]},
        ).scalar_one()
        cfg = session.execute(
            text("SELECT COUNT(*) FROM project_configurations WHERE project_id = :id"),
            {"id": created["id"]},
        ).scalar_one()
    assert remaining == 0
    assert cfg == 0


def test_delete_unknown_id_returns_404(client: TestClient) -> None:
    r = client.delete(f"/api/v1/projects/{uuid4()}")

    assert r.status_code == 404

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID

from app.db.base import Base
from app.db.models import ProjectConfigurationModel, ProjectModel  # noqa: F401


def _projects():
    return Base.metadata.tables["projects"]


def _configs():
    return Base.metadata.tables["project_configurations"]


def test_tables_registered() -> None:
    assert "projects" in Base.metadata.tables
    assert "project_configurations" in Base.metadata.tables


def test_projects_columns() -> None:
    cols = _projects().c
    assert cols["id"].primary_key is True
    assert isinstance(cols["id"].type, PgUUID)
    assert cols["name"].nullable is False
    assert cols["description"].nullable is True
    assert cols["project_type"].nullable is False
    assert cols["source"].nullable is False
    assert cols["source_reference_id"].nullable is True
    assert cols["status"].nullable is False
    assert cols["created_by"].nullable is False
    assert cols["created_at"].nullable is False
    assert cols["updated_at"].nullable is False


def test_projects_check_constraints_use_convention_names() -> None:
    names = {
        c.name for c in _projects().constraints if isinstance(c, CheckConstraint)
    }
    assert "ck_projects_project_type" in names
    assert "ck_projects_source" in names
    assert "ck_projects_status" in names


def test_projects_status_is_indexed() -> None:
    index_columns = {tuple(i.columns.keys()) for i in _projects().indexes}
    assert ("status",) in index_columns
    assert ("source", "source_reference_id") in index_columns


def test_configuration_foreign_key_cascades() -> None:
    fks = list(_configs().c["project_id"].foreign_keys)
    assert len(fks) == 1
    assert fks[0].target_fullname == "projects.id"
    assert fks[0].ondelete == "CASCADE"


def test_configuration_project_id_is_unique() -> None:
    uqs = [c for c in _configs().constraints if isinstance(c, UniqueConstraint)]
    assert any(
        list(c.columns.keys()) == ["project_id"] for c in uqs
    ), "expected a UNIQUE(project_id) enforcing 1:1"


def test_configuration_tech_stack_is_jsonb() -> None:
    assert isinstance(_configs().c["tech_stack"].type, JSONB)


def test_configuration_prose_fields_are_not_null() -> None:
    cols = _configs().c
    for field in ("context", "goals", "scope", "constraints", "coding_standards"):
        assert cols[field].nullable is False, field
    assert cols["tech_stack"].nullable is False

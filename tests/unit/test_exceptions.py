import pytest

from app.exceptions.project import (
    ProjectCreationError,
    ProjectError,
    ProjectValidationError,
)


def test_hierarchy() -> None:
    assert issubclass(ProjectValidationError, ProjectError)
    assert issubclass(ProjectCreationError, ProjectError)


def test_validation_error_carries_field_context() -> None:
    err = ProjectValidationError("must be non-empty", field="name")

    assert err.message == "must be non-empty"
    assert err.field == "name"
    assert str(err) == "[name] must be non-empty"


def test_validation_error_without_field() -> None:
    err = ProjectValidationError("bad payload")

    assert err.field is None
    assert str(err) == "bad payload"


def test_creation_error_preserves_cause_chain() -> None:
    original = RuntimeError("db exploded")

    with pytest.raises(ProjectCreationError) as excinfo:
        try:
            raise original
        except RuntimeError as exc:
            raise ProjectCreationError("could not persist project") from exc

    assert excinfo.value.message == "could not persist project"
    assert excinfo.value.__cause__ is original

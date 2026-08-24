import pytest

from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType


def test_project_type_values() -> None:
    assert {e.value for e in ProjectType} == {"NEW", "EXISTING"}


def test_project_source_values() -> None:
    assert {e.value for e in ProjectSource} == {"PPM", "OTHER"}


def test_project_status_values() -> None:
    assert {e.value for e in ProjectStatus} == {"DRAFT", "ACTIVE", "ARCHIVED"}


def test_str_enum_equals_underlying_string() -> None:
    assert ProjectType.NEW == "NEW"
    assert ProjectStatus.DRAFT == "DRAFT"


def test_construction_from_string_succeeds() -> None:
    assert ProjectType("EXISTING") is ProjectType.EXISTING
    assert ProjectSource("PPM") is ProjectSource.PPM


def test_construction_from_unknown_string_raises() -> None:
    with pytest.raises(ValueError):
        ProjectType("UNKNOWN")

    with pytest.raises(ValueError):
        ProjectStatus("COMPLETED")

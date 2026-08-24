from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput


def _valid_config() -> CreateProjectConfigurationInput:
    return CreateProjectConfigurationInput(
        context="ctx",
        goals="goals",
        scope="scope",
        constraints="none",
        tech_stack={"backend": ["Python"]},
        coding_standards="PEP 8",
    )


def test_create_project_input_defaults_optional_fields_to_none() -> None:
    payload = CreateProjectInput(
        name="X",
        project_type="NEW",
        source="PPM",
        created_by="user-1",
        configuration=_valid_config(),
    )

    assert payload.description is None
    assert payload.source_reference_id is None


def test_create_project_input_accepts_optional_fields() -> None:
    payload = CreateProjectInput(
        name="X",
        project_type="NEW",
        source="PPM",
        created_by="user-1",
        configuration=_valid_config(),
        description="hello",
        source_reference_id="PPM-42",
    )

    assert payload.description == "hello"
    assert payload.source_reference_id == "PPM-42"


def test_create_project_input_is_mutable() -> None:
    payload = CreateProjectInput(
        name="X",
        project_type="NEW",
        source="PPM",
        created_by="user-1",
        configuration=_valid_config(),
    )

    payload.name = "Y"
    assert payload.name == "Y"

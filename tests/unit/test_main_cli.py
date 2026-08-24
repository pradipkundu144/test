import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.main import _parse_config_json, _project_to_dict, build_parser, main


def _valid_config_json() -> str:
    return json.dumps(
        {
            "context": "ctx",
            "goals": "goals",
            "scope": "scope",
            "constraints": "none",
            "tech_stack": {"backend": ["Python"]},
            "coding_standards": "PEP 8",
        }
    )


def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    assert exit_code == 0
    assert "Synapse" in capsys.readouterr().out


def test_help_flag_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    assert "create-project" in capsys.readouterr().out


def test_create_project_help_lists_required_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        main(["create-project", "--help"])

    out = capsys.readouterr().out
    for flag in ("--name", "--project-type", "--source", "--created-by", "--config-json"):
        assert flag in out


def test_missing_settings_exits_with_config_code(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # avoid picking up the developer's real .env
    monkeypatch.setattr("app.main.load_dotenv", lambda *_a, **_k: None)

    exit_code = main(
        [
            "create-project",
            "--name", "X",
            "--project-type", "NEW",
            "--source", "PPM",
            "--created-by", "u",
            "--config-json", _valid_config_json(),
        ]
    )

    assert exit_code == 4
    assert "Configuration error" in capsys.readouterr().err


def test_parse_config_json_accepts_valid_payload() -> None:
    config = _parse_config_json(_valid_config_json())

    assert config.context == "ctx"
    assert config.tech_stack == {"backend": ["Python"]}


def test_parse_config_json_rejects_malformed_json() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_config_json("{not json")


def test_parse_config_json_rejects_non_object() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        _parse_config_json('["a", "b"]')


def test_parse_config_json_rejects_missing_keys() -> None:
    with pytest.raises(ValueError, match="missing keys"):
        _parse_config_json(json.dumps({"context": "c"}))


def test_project_to_dict_serialization_shape() -> None:
    now = datetime.now(UTC)
    pid = uuid4()
    config = ProjectConfiguration(
        id=uuid4(),
        project_id=pid,
        context="c",
        goals="g",
        scope="s",
        constraints="none",
        tech_stack={"a": 1},
        coding_standards="std",
        created_at=now,
        updated_at=now,
    )
    project = Project(
        id=pid,
        name="X",
        description="d",
        project_type=ProjectType.NEW,
        source=ProjectSource.PPM,
        source_reference_id="R",
        status=ProjectStatus.DRAFT,
        created_by="u",
        created_at=now,
        updated_at=now,
        configuration=config,
    )

    result = _project_to_dict(project)

    assert result["id"] == str(pid)
    assert result["project_type"] == "NEW"
    assert result["source"] == "PPM"
    assert result["status"] == "DRAFT"
    assert result["created_at"] == now.isoformat()
    assert result["configuration"]["project_id"] == str(pid)
    assert result["configuration"]["tech_stack"] == {"a": 1}
    assert json.dumps(result)

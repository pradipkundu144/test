import json
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import main


@pytest.fixture(autouse=True)
def _reset_tables(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        session.execute(text("TRUNCATE projects CASCADE"))
        session.commit()


def _config_json() -> str:
    return json.dumps(
        {
            "context": "cli context",
            "goals": "cli goals",
            "scope": "cli scope",
            "constraints": "cli constraints",
            "tech_stack": {"backend": ["Python"], "db": ["PostgreSQL"]},
            "coding_standards": "PEP 8",
        }
    )


def test_cli_creates_project_and_prints_json(
    session_factory: sessionmaker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "create-project",
            "--name", "CLI Project",
            "--project-type", "NEW",
            "--source", "PPM",
            "--created-by", "cli-user",
            "--description", "Made from the CLI",
            "--source-reference-id", "PPM-CLI-1",
            "--config-json", _config_json(),
        ]
    )

    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "CLI Project"
    assert payload["status"] == "DRAFT"
    assert payload["configuration"]["tech_stack"] == {
        "backend": ["Python"],
        "db": ["PostgreSQL"],
    }

    project_id = UUID(payload["id"])
    with session_factory() as session:
        row = session.execute(
            text("SELECT name, status FROM projects WHERE id = :id"),
            {"id": project_id},
        ).one()
        assert row.name == "CLI Project"
        assert row.status == "DRAFT"

        cfg = session.execute(
            text(
                "SELECT project_id, context, tech_stack "
                "FROM project_configurations WHERE project_id = :id"
            ),
            {"id": project_id},
        ).one()
        assert cfg.project_id == project_id
        assert cfg.context == "cli context"
        assert cfg.tech_stack == {"backend": ["Python"], "db": ["PostgreSQL"]}


def test_cli_reports_validation_error_for_invalid_source(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "create-project",
            "--name", "X",
            "--project-type", "NEW",
            "--source", "NOPE",
            "--created-by", "u",
            "--config-json", _config_json(),
        ]
    )

    assert exit_code == 2
    assert "[source]" in capsys.readouterr().err


def test_cli_reports_validation_error_for_bad_config_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "create-project",
            "--name", "X",
            "--project-type", "NEW",
            "--source", "PPM",
            "--created-by", "u",
            "--config-json", "{not-json",
        ]
    )

    assert exit_code == 2
    assert "not valid JSON" in capsys.readouterr().err

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from app.config.settings import Settings, SettingsError, load_dotenv, load_settings
from app.db.session import create_engine_from_settings, create_session_factory
from app.domain.entities.project import Project
from app.exceptions.project import ProjectCreationError, ProjectValidationError
from app.logging.logger import configure_logging, get_logger
from app.repositories.project_repository import SqlAlchemyProjectRepository
from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput
from app.services.project_service import ProjectService


EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_CREATION = 3
EXIT_CONFIG = 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.main",
        description="Synapse — Project Intake service.",
    )
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser(
        "create-project",
        help="Create a Synapse project (DRAFT) and its initial configuration.",
    )
    create.add_argument("--name", required=True)
    create.add_argument("--project-type", required=True, help="NEW | EXISTING")
    create.add_argument("--source", required=True, help="PPM | OTHER")
    create.add_argument("--created-by", required=True)
    create.add_argument("--description", default=None)
    create.add_argument("--source-reference-id", default=None)
    create.add_argument(
        "--config-json",
        required=True,
        help=(
            "JSON object with keys: context, goals, scope, constraints, "
            "tech_stack (object), coding_standards"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return EXIT_OK

    load_dotenv()
    try:
        settings = load_settings()
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    configure_logging(settings.log_level)

    if args.command == "create-project":
        return _cmd_create_project(args, settings)

    parser.print_help()
    return EXIT_OK


def _cmd_create_project(args: argparse.Namespace, settings: Settings) -> int:
    try:
        configuration = _parse_config_json(args.config_json)
    except ValueError as exc:
        print(f"[--config-json] {exc}", file=sys.stderr)
        return EXIT_VALIDATION

    payload = CreateProjectInput(
        name=args.name,
        project_type=args.project_type,
        source=args.source,
        created_by=args.created_by,
        configuration=configuration,
        description=args.description,
        source_reference_id=args.source_reference_id,
    )

    engine = create_engine_from_settings(settings)
    try:
        service = ProjectService(
            create_session_factory(engine),
            SqlAlchemyProjectRepository,
        )
        try:
            project = service.create_project(payload)
        except ProjectValidationError as exc:
            location = f"[{exc.field}] " if exc.field else ""
            print(f"Validation error: {location}{exc.message}", file=sys.stderr)
            return EXIT_VALIDATION
        except ProjectCreationError as exc:
            print(f"Creation failed: {exc.message}", file=sys.stderr)
            return EXIT_CREATION
    finally:
        engine.dispose()

    print(json.dumps(_project_to_dict(project), indent=2))
    return EXIT_OK


def _parse_config_json(raw: str) -> CreateProjectConfigurationInput:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"not valid JSON ({exc.msg})") from exc

    if not isinstance(data, dict):
        raise ValueError("must be a JSON object")

    required = {"context", "goals", "scope", "constraints", "tech_stack", "coding_standards"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

    return CreateProjectConfigurationInput(
        context=data["context"],
        goals=data["goals"],
        scope=data["scope"],
        constraints=data["constraints"],
        tech_stack=data["tech_stack"],
        coding_standards=data["coding_standards"],
    )


def _project_to_dict(project: Project) -> dict[str, Any]:
    config = project.configuration
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type.value,
        "source": project.source.value,
        "source_reference_id": project.source_reference_id,
        "status": project.status.value,
        "created_by": project.created_by,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "configuration": {
            "id": str(config.id),
            "project_id": str(config.project_id),
            "context": config.context,
            "goals": config.goals,
            "scope": config.scope,
            "constraints": config.constraints,
            "tech_stack": config.tech_stack,
            "coding_standards": config.coding_standards,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())

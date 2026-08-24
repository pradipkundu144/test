# Synapse — ERD and Project Creation Flow

## Entity–Relationship Diagram

```mermaid
erDiagram
    PROJECTS ||--|| PROJECT_CONFIGURATIONS : "1 : 1 (UNIQUE FK)"

    PROJECTS {
        uuid id PK
        varchar name "NOT NULL"
        text description "NULL"
        varchar project_type "CHECK IN (NEW, EXISTING)"
        varchar source "CHECK IN (PPM, OTHER)"
        varchar source_reference_id "NULL"
        varchar status "CHECK IN (DRAFT, ACTIVE, ARCHIVED), indexed"
        varchar created_by "NOT NULL"
        timestamptz created_at "DEFAULT now()"
        timestamptz updated_at "DEFAULT now(), onupdate now()"
    }

    PROJECT_CONFIGURATIONS {
        uuid id PK
        uuid project_id FK "NOT NULL, UNIQUE, ON DELETE CASCADE"
        text context "NOT NULL"
        text goals "NOT NULL"
        text scope "NOT NULL"
        text constraints "NOT NULL"
        jsonb tech_stack "NOT NULL"
        text coding_standards "NOT NULL"
        timestamptz created_at "DEFAULT now()"
        timestamptz updated_at "DEFAULT now(), onupdate now()"
    }
```

Notes:
- `UNIQUE(project_id)` on `project_configurations` enforces the 1:1 at the DB level.
- Additional composite index on `projects(source, source_reference_id)` for lookups by originating system.
- Enum values live in `app/domain/enums/project.py` as `StrEnum`s and are the single source of truth for both CHECK constraints and service validation.

## Project Creation Flow

```mermaid
flowchart TD
    A["CLI<br/>python -m app.main create-project"] --> B[argparse]
    B --> C["Parse --config-json"]
    C --> D[Build CreateProjectInput]
    D --> E["ProjectService.create_project(payload)"]

    E --> F{Validate<br/>name, created_by, enums,<br/>configuration fields, tech_stack}
    F -->|fail| G["ProjectValidationError<br/>exit 2"]

    F -->|ok| H["Build Project + ProjectConfiguration entities<br/>uuid4(), datetime.now(UTC), status=DRAFT"]
    H --> I["session = session_factory()"]
    I --> J["BEGIN"]
    J --> K["SqlAlchemyProjectRepository.add(project)<br/>maps entity → model, session.add"]
    K --> L{Persist}
    L -->|SQLAlchemyError| M["ROLLBACK<br/>ProjectCreationError raised from exc<br/>exit 3"]
    L -->|ok| N["COMMIT<br/>(context manager exit)"]

    N --> O[Return Project entity]
    O --> P["_project_to_dict → json.dumps<br/>stdout · exit 0<br/>logs on stderr"]
```

Layering (framework-independent):

```
CLI (app.main)
    ↓
ProjectService              business rules + transaction ownership
    ↓
AbstractProjectRepository   contract; SqlAlchemyProjectRepository implements
    ↓
SQLAlchemy 2.x
    ↓
PostgreSQL 16
```

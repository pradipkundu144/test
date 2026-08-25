# Synapse — ERD and Request Flow

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

- `UNIQUE(project_id)` on `project_configurations` enforces the 1:1 at the DB level.
- Composite index on `projects(source, source_reference_id)` for lookups by originating system.
- Enum values live in `app/domain/enums/project.py` as `StrEnum`s — single source of truth for both CHECK constraints and service validation.

## API Request Flow (Create Project)

```mermaid
flowchart TD
    A["POST /api/v1/projects<br/>JSON body"] --> B["FastAPI router<br/>app/api/v1/projects.py"]
    B --> C["ProjectCreateBody<br/>Pydantic v2 validation"]
    C -->|invalid| D["422 project_validation_error"]

    C -->|ok| E["body.to_input() → CreateProjectInput"]
    E --> F["ProjectService.create_project(payload)"]

    F --> G{Domain validation<br/>name, enums, config fields}
    G -->|fail| H["ProjectValidationError<br/>→ 422 project_validation_error"]

    G -->|ok| I["Build Project + Configuration entities<br/>uuid4(), datetime.now(UTC), status=DRAFT"]
    I --> J["session = session_factory()"]
    J --> K["BEGIN"]
    K --> L["SqlAlchemyProjectRepository.add(project)<br/>entity → model, session.add"]
    L --> M{Persist}
    M -->|SQLAlchemyError| N["ROLLBACK<br/>ProjectCreationError<br/>→ 500 project_persistence_error"]
    M -->|ok| O["COMMIT"]

    O --> P["ProjectResponse.from_entity"]
    P --> Q["201 Created + JSON body"]
```

## API Request Flow (Update / Delete)

```mermaid
flowchart TD
    A["PATCH or DELETE<br/>/api/v1/projects/{id}"] --> B["FastAPI router"]
    B --> C{Route}

    C -->|PATCH| D["ProjectUpdateBody (Pydantic)<br/>model_dump(exclude_unset=True)"]
    D --> E["ProjectService.update_project(id, project_changes, config_changes)"]

    C -->|DELETE| F["ProjectService.delete_project(id)"]

    E --> G["session.begin()"]
    F --> G
    G --> H["repo.get_model_by_id / repo.delete"]
    H --> I{Found?}
    I -->|no| J["ProjectNotFoundError<br/>→ 404 project_not_found"]
    I -->|yes| K["Mutate model / mark for delete"]
    K --> L["COMMIT"]

    L --> M{Response}
    M -->|PATCH| N["Reload aggregate → 200 + JSON"]
    M -->|DELETE| O["204 No Content"]
```

## Layering (framework-independent core)

```
HTTP client
    ↓
FastAPI router + Pydantic schemas    thin adapter
    ↓
ProjectService                        business rules + transactions
    ↓
AbstractProjectRepository             contract
    ↓
SqlAlchemyProjectRepository (impl)
    ↓
SQLAlchemy 2.x
    ↓
PostgreSQL 16
```

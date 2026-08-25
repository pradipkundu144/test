class ProjectError(Exception):
    # base for every domain error raised by the project service layer
    pass


class ProjectValidationError(ProjectError):
    # raised when input violates project domain rules (before persistence)
    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field

    def __str__(self) -> str:
        return f"[{self.field}] {self.message}" if self.field else self.message


class ProjectNotFoundError(ProjectError):
    # raised when a lookup by id finds nothing
    def __init__(self, project_id: object) -> None:
        message = f"project {project_id} not found"
        super().__init__(message)
        self.message = message
        self.project_id = project_id


class ProjectPersistenceError(ProjectError):
    # base for any DB-level failure after validation succeeded;
    # always chain the underlying exception with `raise ... from exc` so we
    # keep the cause without leaking driver/ORM types to callers.
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProjectCreationError(ProjectPersistenceError):
    # persistence failure specifically during creation
    pass

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


class ProjectCreationError(ProjectError):
    # raised when persistence fails after validation succeeded;
    # always chain the underlying exception with `raise ... from exc` so we
    # keep the cause without leaking driver/ORM types to callers.
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

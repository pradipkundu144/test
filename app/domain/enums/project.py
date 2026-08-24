from enum import StrEnum


class ProjectType(StrEnum):
    NEW = "NEW"
    EXISTING = "EXISTING"


class ProjectSource(StrEnum):
    PPM = "PPM"
    OTHER = "OTHER"


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

from dataclasses import dataclass
from typing import Any


@dataclass
class CreateProjectConfigurationInput:
    context: str
    goals: str
    scope: str
    constraints: str
    tech_stack: dict[str, Any]
    coding_standards: str


@dataclass
class CreateProjectInput:
    name: str
    project_type: str
    source: str
    created_by: str
    configuration: CreateProjectConfigurationInput
    description: str | None = None
    source_reference_id: str | None = None

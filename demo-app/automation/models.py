from typing import Any, Literal
from pydantic import BaseModel, Field


class Target(BaseModel):
    """
    Describes an element on the application screen.
    """
    kind: Literal["label", "text", "role"]
    value: str


class Action(BaseModel):
    """
    One action that the automation can perform.
    """
    action: Literal["open", "fill", "click", "read"]
    target: Target | None = None
    value: str | None = None


class CapabilityInput(BaseModel):
    """
    A value supplied when the capability is replayed.
    """
    name: str
    type: Literal["string", "integer", "number", "boolean"]
    required: bool = True
    sensitive: bool = False


class CapabilityOutput(BaseModel):
    """
    A value produced by the capability.
    """
    name: str
    type: Literal["string", "integer", "number", "boolean"]


class Checkpoint(BaseModel):
    """
    Defines how we know the automation succeeded.
    """
    contains_text: str


class CapabilityArtifact(BaseModel):
    """
    The reusable workflow produced after successful discovery.
    """
    schema_version: str = "1.0"
    capability_id: str
    capability_version: str = "1.0"

    name: str
    description: str

    inputs: list[CapabilityInput] = Field(default_factory=list)
    outputs: list[CapabilityOutput] = Field(default_factory=list)

    steps: list[Action]

    success_checkpoint: Checkpoint
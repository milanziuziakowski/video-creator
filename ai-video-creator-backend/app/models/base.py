"""Shared Pydantic base model with camelCase aliases."""

from pydantic import BaseModel


def to_camel(string: str) -> str:
    """Convert snake_case string to camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class APIModel(BaseModel):
    """Base model that supports camelCase aliases and snake_case input."""

    class Config:
        alias_generator = to_camel
        validate_by_name = True
        populate_by_name = True
        from_attributes = True

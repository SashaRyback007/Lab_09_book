"""Domain models for the book catalog."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class Book:
    """Book entity from Lab 01 domain."""

    title: str
    author: str
    year: int
    pages: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Book:
        return cls(
            title=str(data["title"]),
            author=str(data["author"]),
            year=int(data["year"]),
            pages=int(data["pages"]),
        )

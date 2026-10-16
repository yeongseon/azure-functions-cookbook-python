from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Protocol

from langchain_core.tools import StructuredTool


@dataclass(frozen=True, slots=True)
class Note:
    title: str
    text: str


class NoteLookup(Protocol):
    def lookup(self, query: str) -> str: ...


SAMPLE_NOTES: Final = (
    Note("Project Atlas", "prepare the launch checklist by Friday"),
    Note("Team schedule", "design review is Tuesday at 10:00"),
)


@dataclass(frozen=True, slots=True)
class SampleNoteLookup:
    notes: tuple[Note, ...] = SAMPLE_NOTES

    def lookup(self, query: str) -> str:
        normalized = query.casefold()
        matches = [note for note in self.notes if normalized in note.title.casefold()]
        if not matches:
            return "No sample note matched the query. [sample data]"
        return "\n".join(f"{note.title}: {note.text}. [sample data]" for note in matches)


def build_note_tool(notes: NoteLookup) -> StructuredTool:
    return StructuredTool.from_function(
        func=notes.lookup,
        name="lookup_notes",
        description="Look up clearly labelled sample personal notes by title.",
    )

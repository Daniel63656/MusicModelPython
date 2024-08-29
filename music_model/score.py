from __future__ import annotations
import typing as t
if t.TYPE_CHECKING:
    from typing import Iterable
    from .part import Part


class Score():
    def __init__(self):
        self._parts = []

    def get_parts(self) -> Iterable[Part]:
        return self._parts

    def append_part(self, part: Part):
        self._parts.append(part)
        part._score = self
        part._idx = len(self._parts) - 1

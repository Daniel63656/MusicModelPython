from __future__ import annotations
from .repeat import RepeatManager

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction
    from typing import Iterable
    from .part import Part


class Score():
    def __init__(self):
        self._parts = []
        self._repeat_manager = RepeatManager()

    def get_parts(self) -> Iterable[Part]:
        return self._parts

    def append_part(self, part: Part):
        self._parts.append(part)
        part._score = self
        part._idx = len(self._parts) - 1

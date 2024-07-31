from __future__ import annotations
from .site import Site

import typing as t
if t.TYPE_CHECKING:
    from .part import Part


class Voice(Site):
    def __init__(self):
        super().__init__()
        self._part = None
        self._id = None

    def get_part(self) -> Part:
        return self._part

    def get_id(self) -> int:
        return self._id

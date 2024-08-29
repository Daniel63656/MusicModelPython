from __future__ import annotations
from .collection import SafeDict
from .staff import Staff
from .voice import Voice

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterable, Optional
    from .score import Score


class Part():
    def __init__(self):
        self._score = None
        self._idx = None
        # these will auto-add staffs/voices if querrying a new key
        self._staffs = SafeDict(lambda id: self.insert_staff(id, Staff()))
        self._voices = SafeDict(lambda id: self.insert_voice(id, Voice()))

    def get_score(self) -> Score:
        return self._score

    def get_idx(self) -> int:
        return self._ix

    def get_staffs(self) -> Iterable[Staff]:
        return self._staffs.values()
    
    def get_staff(self, id) -> Optional[Staff]:
        return self._staffs.get(id)
    
    def get_voices(self) -> Iterable[Voice]:
        return self._voices.values()
    
    def get_voice(self, id) -> Optional[Voice]:
        return self._voices.get(id)

    def insert_staff(self, id: int, staff: Staff):
        self._staffs[id] = staff
        staff._part = self
        staff._id = id

    def insert_voice(self, id: int, voice: Voice):
        self._voices[id] = voice
        voice._part = self
        voice._id = id

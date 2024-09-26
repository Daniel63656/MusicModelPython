from sortedcontainers import SortedDict
from .abstract import Range
from typing import Any
 

class ContinuousMap(SortedDict):
    """
    An ordered dictionary that holds values representing continuous ranges. Each range starts at the specified key, 
    and its end is implicitly determined by the start of the next range. These ranges cover the entire key space without gaps or overlaps.
    Keys must be comparable.

    For any given key, the value in effect can be retrieved using []-notation, while `get()` will only return a value if it is
    exactly present at that key.
    """

    def __getitem__(self, key):
        index = self.bisect_right(key) - 1
        if index >= 0:
            return super().__getitem__(self.keys()[index])
        return None
    

class DiscontinuousMap(SortedDict):
    """
    An ordered dictionary that holds discontinuous ranges, meaning there may be gaps between consecutive ranges. 
    Each range must have an explicitly defined start and end, and ranges cannot overlap. Keys must be comparable and values must implement the `Range` interface.

    For any given key, the value in effect (or None) can be retrieved using []-notation, while `get()` will only return a value if it is
    exactly present at that key.
    """
    
    def __setitem__(self, key: Any, value: Range) -> None:
        # enforce Range type for value and check if key matches the onset of the range
        if not isinstance(value, Range):
            raise TypeError("Values must be of type Range")
        assert key == value.get_onset(), "Key must match the onset of the range"
        super().__setitem__(key, value)

    def __getitem__(self, key):
        index = self.bisect_right(key) - 1
        if index >= 0:
            value = super().__getitem__(self.keys()[index])
            if value.encloses(key):
                return value
        return None
    
    def get_by_offset(self, key):
        """ Returns the range if it has an offset at the given key, otherwise returns None. """
        index = self.bisect_left(key) - 1   # get lower entry
        if index >= 0:
            value = super().__getitem__(self.keys()[index])
            if value.get_offset() == key:
                return value
        return None

    
class SafeDict(dict):
    """
    A dictionary that is auto initializes values for querried, but non-existing keys using a custom function.

    factory: lambda mapping key to function
    Example:    dict = SafeDict(lambda x: -x)
                dict[1]     # this creates the pair {1: -1}
    """
    def __init__(self, factory):
        self.factory = factory

    def __missing__(self, key):
        self.factory(key)
        return self[key]

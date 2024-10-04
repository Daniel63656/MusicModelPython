from sortedcontainers import SortedDict
from .abstract import Range
from typing import Any


class SortedMap(SortedDict):
    def higher_entry(self, key):
        """
        Return the smallest value with a key strictly greater than 'key' or None if no such value exists.
        """
        index = self.bisect_right(key)
        if index < len(self):
            return self.keys()[index], super().__getitem__(self.keys()[index])
        return None

    def ceiling_entry(self, key):
        """
        Return the smallest value with a key greater than or equal to 'key' or None if no such value exists.
        """
        index = self.bisect_left(key)
        if index < len(self):
            return self.keys()[index], super().__getitem__(self.keys()[index])
        return None
    
    def lower_entry(self, key):
        """
        Return the largest value with a key strictly less than 'key' or None if no such value exists.
        """
        index = self.bisect_left(key) - 1
        if index >= 0:
            return self.keys()[index], super().__getitem__(self.keys()[index])
        return None

    def floor_entry(self, key):
        """
        Return the largest value with a key less than or equal to 'key' or None if no such value exists.
        """
        index = self.bisect_right(key) - 1
        if index >= 0:
            return self.keys()[index], super().__getitem__(self.keys()[index])
        return None
    
    def index_of(self, key):
        return self.bisect_right(key) - 1
 

class ContinuousMap(SortedMap):
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
        # check for overlaps with higher/lower entry
        higher = self.higher_value(key)
        if higher is not None:
            assert not value.encloses(higher.get_onset()), "New range overlaps with existing range"
        lower = self.lower_value(key)
        if lower is not None:
            assert not lower.encloses(key), "New range overlaps with existing range"
        super().__setitem__(key, value)

    def __getitem__(self, key):
        index = self.bisect_right(key) - 1
        if index >= 0:
            value = super().__getitem__(self.keys()[index])
            if value.encloses(key):
                return value
        return None
    
    def higher_value(self, key):
        """
        Return the smallest value with a key strictly greater than 'key' or None if no such value exists.
        """
        index = self.bisect_right(key)
        if index < len(self):
            return super().__getitem__(self.keys()[index])
        return None

    def ceiling_value(self, key):
        """
        Return the smallest value with a key greater than or equal to 'key' or None if no such value exists.
        """
        # check if exact value exists
        value = self.get(key)
        if value is not None:
            return value
        # if the key doesn't exist, fallback to the first key greater than the input key
        return self.higher_value(key)
    
    def lower_value(self, key):
        """
        Return the largest value with a key strictly less than 'key' or None if no such value exists.
        """
        index = self.bisect_left(key) - 1
        if index >= 0:
            return super().__getitem__(self.keys()[index])
        return None

    def floor_value(self, key):
        """
        Return the largest value with a key less than or equal to 'key' or None if no such value exists.
        """
        # check if exact value exists
        value = self.get(key)
        if value is not None:
            return value
        # if the key doesn't exist, fallback to the largest key smaller than the input key
        return self.lower_value(key)
    
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

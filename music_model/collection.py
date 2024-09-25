from sortedcontainers import SortedDict
from .abstract import Range
from typing import Any
 

class ContinuousMap(SortedDict):
    """ An ordered map that holds ranges that are continuous, meaning their end is implicitly determined by the start of the
        next range or the maximal possible end point if no next range is present. Continuous ranges cover the key-space
        without leaving gaps and without overlapping.
        The value for the current range can be retrieved using []-notation, while get() will only return a value if it is
        exactly present at that key.
        Keys must be comparable.
    """

    def __getitem__(self, key):
        index = self.bisect_right(key) - 1
        if index >= 0:
            return super().__getitem__(self.keys()[index])
        return None
    

class DiscontinuousMap(SortedDict):
    """ An ordered map that holds ranges that are discontinuous, meaning a range might end earlier than the
        next range starts. Or in other words, there can be gaps between discontinuous ranges. Therefore, the end of
        a range must be explicitly defined. Ranges can not overlap.
        The value for the current range (if present) can be retrieved using []-notation, while get() will only return a value if it is
        exactly present at that key.
        Keys must be comparable and values must implement the ```Range``` interface to define their interval in ```encloses()```
    """
    
    # enforce type for values as map uses Range functions
    def __setitem__(self, key: Any, value: Range) -> None:
        if not isinstance(value, Range):
            raise TypeError("Values must be of type Range")
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
    """ A dict that is auto initialized using a custom action if querried key does not exist.
        factory: lambda mapping key to function
        Example:    dict = SafeDict(lambda x: -x)
                    dict[1]     # this creates the pair {1: -1}
    """
    def __init__(self, factory):
        self.factory = factory

    def __missing__(self, key):
        self.factory(key)
        return self[key]

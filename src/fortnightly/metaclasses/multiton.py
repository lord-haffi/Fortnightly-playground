from typing import Any

from frozendict import frozendict


# Don't support POSITIONAL_AND_KEYWORD arguments (i.e. only POSITIONAL_ONLY and KEYWORD_ONLY)


Args = tuple[Any, ...]
Kwargs = frozendict[str, Any]


class MultitonMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.__multiton_instances__: dict[tuple[Args, Kwargs], Any] = {}
        # If you want proper typing here you'd need to create an additional base class to correctly type hint it there.

    def __call__(cls, *args, **kwargs):
        # Check if this set of parameters already has an instance
        kwargs = frozendict(kwargs)
        if (args, kwargs) not in cls.__multiton_instances__:
            cls.__multiton_instances__[args, kwargs] = super().__call__(*args, **kwargs)
        return cls.__multiton_instances__[args, kwargs]


class Multiton(metaclass=MultitonMeta):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs


def test_multiton():
    obj1 = Multiton(1, "test", foo="bar")
    obj2 = Multiton(1, "test", foo="bar")
    obj3 = Multiton(2, "test", foo="bar")
    obj4 = Multiton(1, "test", foo="PLS NOT BAR!")

    assert obj1 is obj2  # Same instance
    assert obj1 is not obj3  # Different instances
    assert obj1 is not obj4  # Different instances


def test_multiton_limitations():
    class MultitonSubclass(Multiton):
        def __init__(self, a: str, b: str, c: int):
            super().__init__()
            self.a = a
            self.b = b
            self.c = c

    obj1 = MultitonSubclass("test", "test", 1)
    obj2 = MultitonSubclass("test", "test", c=1)

    assert obj1 is obj2

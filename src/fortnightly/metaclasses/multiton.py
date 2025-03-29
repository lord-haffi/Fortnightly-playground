import inspect
from typing import Any, Literal

from frozendict import frozendict


# Don't support POSITIONAL_AND_KEYWORD arguments (i.e. only POSITIONAL_ONLY and KEYWORD_ONLY)


Args = tuple[Any, ...]
Kwargs = frozendict[str, Any]


class SimpleMultitonMeta(type):
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


class SimpleMultiton(metaclass=SimpleMultitonMeta):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs


def test_multiton():
    obj1 = SimpleMultiton(1, "test", foo="bar")
    obj2 = SimpleMultiton(1, "test", foo="bar")
    obj3 = SimpleMultiton(2, "test", foo="bar")
    obj4 = SimpleMultiton(1, "test", foo="PLS NOT BAR!")

    assert obj1 is obj2  # Same instance
    assert obj1 is not obj3  # Different instances
    assert obj1 is not obj4  # Different instances


def test_multiton_limitations():
    class MultitonSubclass(SimpleMultiton):
        def __init__(self, a: str, b: str, c: int):
            super().__init__()
            self.a = a
            self.b = b
            self.c = c

    obj1 = MultitonSubclass("test", "test", 1)
    obj2 = MultitonSubclass("test", "test", c=1)

    assert obj1 is obj2


# Now in even better. We will use a kwarg on the metaclass to customize for classes which method should be used
# to bind the arguments on. This way we can support POSITIONAL_AND_KEYWORD arguments.


class MultitonMeta(type):
    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
        *,
        bind_on: Literal["__new__", "__init__"],
    ):
        # We need this __new__ method here because otherwise for some reason Python tries to call
        # Multiton.__init_subclass__ which will fail as it takes no keyword arguments.
        # Don't know why, tbh.
        return super().__new__(cls, name, bases, attrs)

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
        *,
        bind_on: Literal["__new__", "__init__"],
    ):
        super().__init__(name, bases, attrs)
        cls.__multiton_instances__: dict[frozendict[str, Any], Any] = {}
        # If you want proper typing here you'd need to create an additional base class to correctly type hint it there.
        if bind_on not in ("__new__", "__init__"):
            raise ValueError(f"Invalid bind_on value: {bind_on}. Must be '__new__' or '__init__'.")
        cls.__multiton_bind_on__ = getattr(cls, bind_on)

    def __call__(cls, *args, **kwargs):
        # Bind the arguments to the method specified in bind_on
        bound_arguments = inspect.signature(cls.__multiton_bind_on__).bind(None, *args, **kwargs)
        # None is inserted to the first argument, i.e. `self` for __init__ and `cls` for __new__
        # We are only interested in caching the other arguments, so it's fine.
        bound_arguments.apply_defaults()
        params = frozendict(bound_arguments.arguments)
        # It's ok to lose the information about the order here as the arguments cannot have doubled keys

        # Check if this set of parameters already has an instance
        if params not in cls.__multiton_instances__:
            cls.__multiton_instances__[params] = super().__call__(*args, **kwargs)
        return cls.__multiton_instances__[params]


class Multiton(metaclass=MultitonMeta, bind_on="__init__"):
    def __init__(self, a: str, b: str, c: int):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c


def test_superior_multiton():
    class MultitonSubclass(Multiton, bind_on="__init__"):
        def __init__(self, a: str, b: str, c: int):
            super().__init__(a=a, b=b, c=c)

    obj1 = MultitonSubclass("test", "test", 1)
    obj2 = MultitonSubclass("test", "test", c=1)
    obj3 = MultitonSubclass("test", "test", c=1)
    obj4 = MultitonSubclass(a="test", c=1, b="test")
    obj5 = MultitonSubclass("test", "test", 666)

    assert obj1 is obj2 is obj3 is obj4
    assert obj1 is not obj5


def test_multiton_with_bind_on_without_kwarg():
    class IncorrectMultiton(metaclass=MultitonMeta): ...

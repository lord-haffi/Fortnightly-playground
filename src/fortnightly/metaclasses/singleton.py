import inspect

from typing import ClassVar, Any


class SimpleSingleton:
    _instance: ClassVar["SimpleSingleton | None"] = None

    def __new__(cls, *args, **kwargs):
        print("SimpleSingleton.__new__() was called")
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        print("SimpleSingleton.__init__() was called")
        self.args = args
        self.kwargs = kwargs


def test_simple_singleton():
    instance1 = SimpleSingleton("arg1", kwarg1="value1")
    instance2 = SimpleSingleton("arg2", kwarg2="value2")

    assert instance1 is instance2
    assert instance1.args == ("arg1",)  # Will fail!


# Singleton pattern + instantiation arguments doesn't actually make that much of a sense.
# But how *could* we prevent calling __init__() again?

# Generally, it's not possible with "regular" classes to modify which arguments are passed to the __new__
# and which are passed to the __init__ method. We could work around this by using some kind of class variable
# tracker if we are in "instantiation" mode.
# But there is actually a better way to do this.


#
#            ███    ███ ███████ ████████  █████   ██████ ██       █████  ███████ ███████ ███████ ███████
#            ████  ████ ██         ██    ██   ██ ██      ██      ██   ██ ██      ██      ██      ██
#            ██ ████ ██ █████      ██    ███████ ██      ██      ███████ ███████ ███████ █████   ███████
#            ██  ██  ██ ██         ██    ██   ██ ██      ██      ██   ██      ██      ██ ██           ██
#            ██      ██ ███████    ██    ██   ██  ██████ ███████ ██   ██ ███████ ███████ ███████ ███████
#
#
# We will talk about 3 important functions in context of metaclasses:
# __new__
# __init__
# __call__


def test_meta_class_execution_order():
    print("Testing metaclass execution order...")

    class ShoutingMeta(type):
        def __new__(mcs, name, bases, attrs):
            print("ShoutingMeta.__new__() was called")
            return type.__new__(mcs, name, bases, attrs)

        def __init__(cls, name, bases, attrs):
            print("ShoutingMeta.__init__() was called")
            super().__init__(name, bases, attrs)

        def __call__(cls, *args, **kwargs):
            print("ShoutingMeta.__call__() was called")
            instance = super().__call__(*args, **kwargs)
            return instance

    class ShoutingClass(metaclass=ShoutingMeta):
        def __new__(cls, *args, **kwargs):
            print("ShoutingClass.__new__() was called")
            return super().__new__(cls)

        def __init__(self, *args, **kwargs):
            print("ShoutingClass.__init__() was called")
            self.args = args
            self.kwargs = kwargs

    class ShoutingSubClass(ShoutingClass):
        def __new__(cls, *args, **kwargs):
            print("ShoutingSubClass.__new__() was called")
            return super().__new__(cls)

        def __init__(self, *args, **kwargs):
            print("ShoutingSubClass.__init__() was called")
            super().__init__(*args, **kwargs)

    print("Now we will create an instance of ShoutingClass...")
    instance = ShoutingClass("arg1", kwarg1="value1")
    assert instance.args == ("arg1",)
    assert instance.kwargs == {"kwarg1": "value1"}

    print("Now we will create an instance of ShoutingSubClass...")
    instance = ShoutingSubClass("arg2", kwarg2="value2")
    assert instance.args == ("arg2",)
    assert instance.kwargs == {"kwarg2": "value2"}


# Now use metaclass __call__ to customize when to initialize our model


class NotThatSimpleSingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__call__(*args, **kwargs)
        assert isinstance(cls._instance, cls)
        return cls._instance


class NotThatSimpleSingleton(metaclass=NotThatSimpleSingletonMeta):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def test_simple_singleton_meta():
    instance1 = NotThatSimpleSingleton("arg1", kwarg1="value1")
    instance2 = NotThatSimpleSingleton("arg2", kwarg2="value2")

    assert instance1 is instance2
    assert instance1.args == ("arg1",)
    assert instance1.kwargs == {"kwarg1": "value1"}
    assert instance2.args == ("arg1",)


# What if we want to require classes using the metaclass to have no arguments on the constructor?
# We can customize class creation by using __new__ and __init__ on the metaclass.


class SingletonMeta(type):
    __singleton_instance__: Any
    # If you want proper typing here you'd need to create an additional base class to correctly type hint it there.

    def __new__(mcs, name, bases, attrs):
        attrs["__singleton_instance__"] = None

        cls = super().__new__(mcs, name, bases, attrs)

        cls_new_signature = inspect.signature(cls.__new__)
        cls_init_signature = inspect.signature(cls.__init__)
        if (
            cls.__new__ is not object.__new__  # Allow class creation if the class didn't override __new__
            and len(cls_new_signature.parameters) != 1
            or cls.__init__ is not object.__init__
            and len(cls_init_signature.parameters) != 1
        ):
            raise TypeError(f"Classes using {mcs.__name__} as metaclass must not have any constructor arguments")
        return cls

    def __call__(cls, *args, **kwargs):
        if cls.__singleton_instance__ is None:
            cls.__singleton_instance__ = super().__call__(*args, **kwargs)
        assert isinstance(cls.__singleton_instance__, cls)
        return cls.__singleton_instance__


def test_illegal_singleton():
    class IllegalSingleton(metaclass=SingletonMeta):
        def __init__(self, *args, **kwargs):
            pass


def test_correct_singleton():
    class CorrectSingleton(metaclass=SingletonMeta):
        def __init__(self):
            self.args = None
            self.kwargs = None

    instance1 = CorrectSingleton()
    instance2 = CorrectSingleton()

    assert instance1 is instance2
    assert instance1.args is None
    assert instance1.kwargs is None

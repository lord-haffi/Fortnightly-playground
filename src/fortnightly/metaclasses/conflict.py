from abc import ABC, ABCMeta


class SomeAbstractBaseClass(ABC): ...


class MyMetaclass(type): ...


class MyClass(metaclass=MyMetaclass): ...


def test_metaclass_conflict():

    class A(SomeAbstractBaseClass, MyClass): ...


class MyABCMeta(MyMetaclass, ABCMeta): ...


def test_metaclass_conflict_resolved():
    class A(SomeAbstractBaseClass, MyClass, metaclass=MyABCMeta): ...

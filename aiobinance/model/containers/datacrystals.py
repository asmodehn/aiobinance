# frozen dataclass (pydantic for type check)
# Basic record type. Non Empty set of attributes (order shouldn't matter, unicity enforced)

from dataclasses import fields
from typing import Any, Callable, Optional, Type, Union

import hypothesis.strategies as st
from hypothesis import infer


def _str(slf):
    # Human friendly display of dataclasses
    typename = type(slf).__name__
    lines = [f"{typename}", "-" * len(typename)]
    for f in fields(slf):
        lines.append(f"{f.name}: {getattr(slf,f.name)}")

    return "\n".join(lines)


def _dir(slf):
    # only expose fields
    return [f.name for f in fields(slf)]


def _strategy(cls):
    # Strategie inferring attributes from type hints by default

    params = {}

    for f in fields(cls):
        if f.name:
            params.update({f.name: infer})

    return st.builds(cls, **params)


try:
    from pydantic.dataclasses import DataclassT
    from pydantic.dataclasses import dataclass as pydantic_dataclass

    def datacrystal(
        _cls: Optional[Type[Any]] = None,
        *,
        init: bool = True,
        repr: bool = True,
        order: bool = False,
        config: Type[Any] = None,
    ):
        """
        Decorator to wrap a dataclass declaration.
        Relies on Pydantic to provide type verification.

        This is usable as python's dataclass decorator, but also provide more features, along with more strictness
        >>> import decimal
        >>> class SampleDataCrystal:
        ...      attr_int: int
        ...      attr_dec: decimal.Decimal
        >>> SampleDataCrystal = datacrystal(SampleDataCrystal)
        >>> SampleDCInstance = SampleDataCrystal(attr_int= 42, attr_dec=decimal.Decimal("3.1415"))

        datacrystal() provides, on top of pydantic's dataclass:

        Machine output:
        >>> print(repr(SampleDCInstance))
        SampleDataCrystal(attr_int=42, attr_dec=Decimal('3.1415'))

        Human output:
        >>> print(str(SampleDCInstance))
        SampleDataCrystal
        -----------------
        attr_int: 42
        attr_dec: 3.1415

        attributes for introspection retrieving only the declared fields (without potential custom validator)
        >>> dir(SampleDCInstance)
        ['attr_dec', 'attr_int']

        """
        cls = pydantic_dataclass(
            _cls,
            init=init,
            repr=repr,
            eq=True,
            order=order,
            unsafe_hash=False,
            frozen=True,
            config=config,
        )

        # extras for cleaner 'record' class
        setattr(cls, "__str__", _str)
        setattr(cls, "__dir__", _dir)
        setattr(cls, "strategy", classmethod(_strategy))

        return cls


except ImportError as ie:

    print(ie)
    print("WARNING: datacrystals implementation falling back to python's dataclasses.")
    print(
        "WARNING: Everything should work, but you might want to download pydantic instead."
    )

    from dataclasses import dataclass as python_dataclass

    def datacrystal(
        _cls: Optional[Type[Any]] = None,
        *,
        init: bool = True,
        repr: bool = True,
        order: bool = False,
    ):
        """
        Decorator to wrap a dataclass declaration.

        This is usable as python's dataclass decorator, but also provide more features, along with more strictness
        >>> import decimal
        >>> class SampleDataCrystal:
        ...      attr_int: int
        ...      attr_dec: decimal.Decimal
        >>> SampleDataCrystal = datacrystal(SampleDataCrystal)
        >>> SampleDCInstance = SampleDataCrystal(attr_int= 42, attr_dec=decimal.Decimal("3.1415"))

        dataclass() provides, on top of python's dataclass:

        Machine output:
        >>> print(repr(SampleDCInstance))
        SampleDataCrystal(attr_int=42, attr_dec=Decimal('3.1415'))

        Human output:
        >>> print(str(SampleDCInstance))
        SampleDataCrystal
        -----------------
        attr_int: 42
        attr_dec: 3.1415

        attributes for introspection retrieving only the declared fields (without potential custom validator)
        >>> dir(SampleDCInstance)
        ['attr_dec', 'attr_int']

        """
        cls = python_dataclass(
            _cls,
            init=init,
            repr=repr,
            eq=True,
            order=order,
            unsafe_hash=False,
            frozen=True,
        )

        # extras for cleaner class
        setattr(cls, "__str__", _str)
        setattr(cls, "__dir__", _dir)
        setattr(cls, "strategy", classmethod(_strategy))

        return cls


if __name__ == "__main__":
    import doctest

    doctest.testmod()

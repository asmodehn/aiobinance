# frozen dataclass (pydantic for type check)
# Basic record type. Non Empty set of attributes (order shouldn't matter, unicity enforced)

from dataclasses import fields
from typing import Any, Callable, Optional, Type, Union

import hypothesis.strategies as st
from hypothesis import infer


def _str(slf):
    # Human friendly display of dataclasses
    lines = []
    for f in fields(slf):
        lines += f"{f.name}: {getattr(slf,'f.name')}"

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
    from pydantic.dataclasses import Dataclass
    from pydantic.dataclasses import dataclass as pydantic_dataclass

    def dataclass(
        _cls: Optional[Type[Any]] = None,
        *,
        init: bool = True,
        repr: bool = True,
        order: bool = False,
        config: Type[Any] = None,
    ) -> Union[Callable[[Type[Any]], Type["Dataclass"]], Type["Dataclass"]]:
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


except ImportError:
    from dataclasses import dataclass as python_dataclass

    def dataclass(
        _cls: Optional[Type[Any]] = None,
        *,
        init: bool = True,
        repr: bool = True,
        order: bool = False,
    ):
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

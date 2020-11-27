from __future__ import annotations

import decimal

# TODO : some tricky code to detect platform float effective precision....
import typing
from decimal import Decimal


class CurrencyMeta(type):
    def __new__(mcls, name, bases, attrs, *, internal_prec, shown_prec):
        # creating context for arithmetic with this currency...
        decimal_context = decimal.BasicContext
        decimal_context.prec = internal_prec

        extra_attrs = {
            "context": decimal_context,  # precision for Decimal computations
            "decimal_precision": shown_prec,  # precision for string formatting & display
            # TODO : add tickers of related markets to get conversion rates with other currencies...
            "__annotations__": {"amount": Decimal},
        }

        def init(self, *, amount: typing.Union[str, float]):
            if isinstance(amount, float):
                self.amount = self.context.create_decimal_from_float(amount)
            else:
                self.amount = self.context.create_decimal(amount)

        def str(self):
            return f"{self.amount} {type(self)}"

        def repr(self):
            return f"{self.amount} {type(self)}"

        def eq(self, other):
            return type(self) is type(other) and self.amount == other.amount

        def add(self, other):
            if isinstance(other, type(self)):
                return type(self)(amount=self.context.add(self.amount, other.amount))
            else:
                raise RuntimeError(
                    f"Aborting. conversion rate of {type(self)} with {type(other)} unknown."
                )

        methods = {
            "__init__": init,
            "__add__": add,
            "__str__": str,
            "__repr__": repr,
            "__eq__": eq,
        }

        M = super().__new__(mcls, name, bases, {**attrs, **extra_attrs, **methods})

        return M

    # we keep the standard repr to not be confused with python types.
    # But we define a more appropriate __str__ for humans
    def __str__(cls):
        return f"{cls.__name__}"


if __name__ == "__main__":

    class BTC(metaclass=CurrencyMeta, internal_prec=8, shown_prec=4):
        pass

    class ETH(metaclass=CurrencyMeta, internal_prec=8, shown_prec=4):
        pass

    print(BTC)
    print(ETH)

    cash1 = BTC("10.0")
    cash2 = ETH("10.0")

    print(cash1)
    print(cash2)

    print(cash1 + cash1)  # works

    print(cash1 + cash2)  # static types dont match, and dynamically breaks

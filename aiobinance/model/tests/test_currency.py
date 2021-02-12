import unittest

from aiobinance.model.currency import CurrencyMeta


class TestCurrencyMeta(unittest.TestCase):

    # Testing on an example for simplicity
    def setUp(self) -> None:
        self.currencySampleA = CurrencyMeta(
            "SampleA", (), {}, internal_prec=8, shown_prec=4
        )
        self.currencySampleB = CurrencyMeta(
            "SampleB", (), {}, internal_prec=8, shown_prec=4
        )

    def test_repr(self):
        assert (
            repr(self.currencySampleA) == "<class 'aiobinance.model.currency.SampleA'>"
        )
        assert (
            repr(self.currencySampleB) == "<class 'aiobinance.model.currency.SampleB'>"
        )

    def test_str(self):
        assert str(self.currencySampleA) == "SampleA"
        assert str(self.currencySampleB) == "SampleB"


class TestCurrency(unittest.TestCase):

    # Testing on an example for simplicity
    def setUp(self) -> None:
        self.currencySampleA = CurrencyMeta(
            "SampleA", (), {}, internal_prec=8, shown_prec=4
        )
        self.currencySampleB = CurrencyMeta(
            "SampleB", (), {}, internal_prec=8, shown_prec=4
        )

    def test_init_float(self):
        v = self.currencySampleA(amount=0.1)
        assert v

    def test_init_str(self):
        v = self.currencySampleA(amount="0.1")
        assert v

    def test_repr(self):
        v = self.currencySampleA(amount=0.1)
        assert repr(v)

    def test_str(self):
        v = self.currencySampleA(amount=0.1)
        assert str(v)

    def test_add_success(self):
        v = self.currencySampleA(amount=0.1)
        w = self.currencySampleA(amount=0.1)

        assert w + v == self.currencySampleA(amount=0.2)

    def test_add_failed(self):
        v = self.currencySampleA(amount=0.1)
        w = self.currencySampleB(amount=0.1)

        with self.assertRaises(RuntimeError) as res_error:
            v + w
        assert (
            res_error.exception.args[0]
            == "Aborting. conversion rate of SampleA with SampleB unknown."
        )


if __name__ == "__main__":
    unittest.main()

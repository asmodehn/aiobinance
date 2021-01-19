import unittest
from datetime import timedelta

from hypothesis import given
from hypothesis import strategies as st

from aiobinance.api.model.timeinterval import TimeIntervalDelta, TimeStep


class TestTimeStep(unittest.TestCase):
    @given(tdelta=st.one_of(st.none(), st.timedeltas()))
    def test_init_values(self, tdelta):
        ts = TimeStep(tdelta)

        # checking tdelta is less than the middle of the timedelta interval and verify matching value.
        if (
            tdelta is None
            or tdelta <= (timedelta(minutes=3) + timedelta(minutes=1)) / 2
        ):
            assert ts.delta == TimeIntervalDelta.minutely
            assert ts.to_api() == "1m"
        elif tdelta <= (timedelta(minutes=5) + timedelta(minutes=3)) / 2:
            assert ts.delta == TimeIntervalDelta.minutely_3
            assert ts.to_api() == "3m"
        elif tdelta <= (timedelta(minutes=15) + timedelta(minutes=5)) / 2:
            assert ts.delta == TimeIntervalDelta.minutely_5
            assert ts.to_api() == "5m"
        elif tdelta <= (timedelta(minutes=30) + timedelta(minutes=15)) / 2:
            assert ts.delta == TimeIntervalDelta.minutely_15
            assert ts.to_api() == "15m"
        elif tdelta <= (timedelta(hours=1) + timedelta(minutes=30)) / 2:
            assert ts.delta == TimeIntervalDelta.minutely_30
            assert ts.to_api() == "30m"
        elif tdelta <= (timedelta(hours=2) + timedelta(hours=1)) / 2:
            assert ts.delta == TimeIntervalDelta.hourly
            assert ts.to_api() == "1h"
        elif tdelta <= (timedelta(hours=4) + timedelta(hours=2)) / 2:
            assert ts.delta == TimeIntervalDelta.hourly_2
            assert ts.to_api() == "2h"
        elif tdelta <= (timedelta(hours=6) + timedelta(hours=4)) / 2:
            assert ts.delta == TimeIntervalDelta.hourly_4
            assert ts.to_api() == "4h"
        elif tdelta <= (timedelta(hours=8) + timedelta(hours=6)) / 2:
            assert ts.delta == TimeIntervalDelta.hourly_6
            assert ts.to_api() == "6h"
        elif tdelta <= (timedelta(hours=12) + timedelta(hours=8)) / 2:
            assert ts.delta == TimeIntervalDelta.hourly_8
            assert ts.to_api() == "8h"
        elif tdelta <= (timedelta(days=1) + timedelta(hours=12)) / 2:
            assert ts.delta == TimeIntervalDelta.hourly_12
            assert ts.to_api() == "12h"
        elif tdelta <= (timedelta(days=3) + timedelta(days=1)) / 2:
            assert ts.delta == TimeIntervalDelta.daily
            assert ts.to_api() == "1d"
        elif tdelta <= (timedelta(weeks=1) + timedelta(days=3)) / 2:
            assert ts.delta == TimeIntervalDelta.daily_3
            assert ts.to_api() == "3d"
        else:
            assert ts.delta == TimeIntervalDelta.weekly
            assert ts.to_api() == "1w"

    @given(tdelta=st.one_of(st.none(), st.timedeltas()))
    def test_hashability_equality(self, tdelta):
        """ this is required to be able to use TimeStep as dict keys """
        ts = TimeStep(tdelta)

        assert hash(ts) == hash(ts)

        assert ts == ts

        tsbis = TimeStep(tdelta)

        assert hash(ts) == hash(tsbis)

        assert ts == tsbis

        # We also have, perhaps less intuitively, equality with delta
        # TODO : useful or confusing ?
        td = ts.delta

        assert hash(ts) == hash(td)

        assert ts == td

    # TODO: TimeInterval tests
    # @given(tdelta=st.one_of(st.none(), st.timedeltas()))
    # def test_union(self, tdelta):
    #     raise NotImplementedError


if __name__ == "__main__":
    unittest.main()

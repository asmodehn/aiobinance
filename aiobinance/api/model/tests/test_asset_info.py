import unittest

from hypothesis import given

from aiobinance.api.model.asset_info import AssetInfo, NetworkInfo


class TestNetworkInfo(unittest.TestCase):
    @given(mi=NetworkInfo.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, mi):

        assert isinstance(mi, NetworkInfo)


class TestAssetInfo(unittest.TestCase):
    @given(mi=AssetInfo.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, mi):

        assert isinstance(mi, AssetInfo)

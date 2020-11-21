import unittest
from dataclasses import fields

import hypothesis.strategies as st
from hypothesis import given

# strategy to build dataclasses dynamically
from aiobinance.model.containers.datacrystals import datacrystal


@st.composite
def st_dcls(
    draw, names=st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll"]))
):  # TODO : character strategy for legal python identifier ??

    attrs = draw(
        st.dictionaries(
            keys=st.text(),
            values=st.one_of(
                st.integers(),
                st.floats(),
                st.decimals(),
                st.text(),
                # etc. TODO support more...
            ),
        )
    )

    dcls = datacrystal(type(draw(names), (), attrs))

    return dcls


class TestDataclassExample(unittest.TestCase):
    @given(dcls=st_dcls(), data=st.data())
    def test_str(self, dcls, data):
        # generating an instance of dcls
        dcinst = data.draw(dcls.strategy())

        dcstr = str(dcinst)

        assert type(dcinst).__name__ in dcstr

        for f in fields(dcinst):
            assert f"{f.name}: {getattr(dcinst, 'f.name')}" in dcstr

    @given(dcls=st_dcls(), data=st.data())
    def test_dir(self, dcls, data):
        # generating an instance of dcls
        dcinst = data.draw(dcls.strategy())

        expected = {f for f in fields(dcinst)}

        dcdir = dir(dcinst)

        assert {a for a in dcdir}.issuperset(expected), expected.difference(
            {a for a in dcdir}
        )

        # check no extra information is exposed
        assert {a for a in dcdir if not a.startswith("__")}.issubset(expected), {
            a for a in dcdir if not a.startswith("__")
        }.difference(expected)

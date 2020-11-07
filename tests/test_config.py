import tempfile

import hypothesis.strategies as st
import pytest
from hypothesis import given

from aiobinance.config import (
    Credentials,
    credentials_strategy,
    load_api_keyfile,
    save_api_keyfile,
)


def test_load_api_keyfile():
    # make temporary file with hummingbot csv format
    """ Loading handcrafted keyfile, following a specific format """
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write("my_user_apikey\nmy_user_secret")
        fp.seek(0)

        creds = load_api_keyfile(fp.name)

        assert creds.key == "my_user_apikey"
        assert creds.secret == "my_user_secret"


@given(creds=credentials_strategy())
def test_credentials_dataclass(creds):

    if creds.secret not in creds.key:
        assert creds.secret not in str(creds)
    assert creds.key in str(creds)

    if creds.secret not in creds.key:
        assert creds.secret not in repr(creds)
    assert creds.key in repr(creds)


@given(creds=credentials_strategy())
def test_save_api_keyfile(creds):
    """ Saving, and then loading, the keyfile """

    with tempfile.NamedTemporaryFile(mode="r") as fp:
        saved_creds = save_api_keyfile(credentials=creds, filepath=fp.name)

        assert saved_creds.key == creds.key
        assert saved_creds.secret == creds.secret


if __name__ == "__main__":
    pytest.main(["-s", __file__])

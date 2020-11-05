import pytest

from aiobinance.decorators import require_auth


def test_require_auth():
    @require_auth(mock_key="key_mocked", mock_secret="secret_mocked")
    def wrappedtest(*args, **kwargs):
        return args, kwargs

    assert wrappedtest() == ((), {"key": "key_mocked", "secret": "secret_mocked"})
    assert wrappedtest(key="mykey") == ((), {"key": "mykey", "secret": None})
    assert wrappedtest(key="mykey", secret="mysecret") == (
        (),
        {"key": "mykey", "secret": "mysecret"},
    )
    assert wrappedtest(secret="mysecret") == ((), {"key": None, "secret": "mysecret"})


if __name__ == "__main__":
    pytest.main(["-s", __file__])

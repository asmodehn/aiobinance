import pytest

from aiobinance.decorators import require_auth


def test_require_auth():

    @require_auth(mock_key="key_mocked", mock_secret="secret_mocked")
    def wrappedtest(*args, **kwargs):
        return args, kwargs

    assert wrappedtest() == ((), {'key': 'key_mocked', 'secret': "secret_mocked"})


if __name__ == "__main__":
    pytest.main(['-s', __file__])

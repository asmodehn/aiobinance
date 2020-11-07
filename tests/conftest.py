import pytest

from aiobinance import config


def pytest_addoption(parser):
    parser.addoption(
        "--with-keyfile",
        action="store_true",
        default=False,
        help="run tests with private key",
    )


@pytest.fixture
def keyfile(request):
    kf = request.config.getoption("--with-keyfile")
    from aiobinance.config import Credentials, load_api_keyfile

    keystruct = Credentials(key="APIkey", secret="S3cr3T")
    # in case we have no keyfile setup, we return values to be passed
    # so that we avoid the defaults, but these can be used to replay network content safely (key not required locally).

    if kf:
        keystruct = load_api_keyfile()

    return keystruct


# TODO : disable rate limiter when testing with replay...

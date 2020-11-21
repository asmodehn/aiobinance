import os

import pytest
from hypothesis import Verbosity, settings

# defining profiles for hypothesis
settings.register_profile("ci", max_examples=1000, deadline=None)
settings.register_profile("dev", max_examples=10)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)
settings.load_profile(os.getenv(u"HYPOTHESIS_PROFILE", "default"))

if os.getenv("CI"):  # set by github actions
    settings.load_profile("ci")


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

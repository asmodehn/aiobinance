import configparser
import inspect
import logging
import os
from typing import Optional

import hypothesis.strategies as st

# Resolve userpath to an absolute path
from pydantic import validator, validators
from pydantic.dataclasses import dataclass

DEFAULT_BINANCE_API_KEYFILE = os.path.expanduser("~/.config/aiobinance/binance.key")

# If the environment variable is set, override the default value
BINANCE_API_KEYFILE = os.getenv("AIOBINANCE_API_KEYFILE", DEFAULT_BINANCE_API_KEYFILE)
BINANCE_API_KEYFILE = os.path.normpath(BINANCE_API_KEYFILE)

logger = logging.getLogger("aiobinance.config")


@dataclass
class Credentials:
    # Note : Credential MUST be created, but both of these should be None to signal a public connection
    key: Optional[str] = None
    secret: Optional[str] = None

    @validator("key", "secret")
    def min_size_creds(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError("too small (len < 5)")
        return v

    def __repr__(self):
        return f"{self.key}"

    def __bool__(self):
        # return false if both are set to none (unauthenticated)
        return self.key is not None or self.secret is not None


def credentials_strategy():
    return st.builds(
        Credentials,
        key=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=5
        ),
        secret=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=5
        ),
    )


def load_api_keyfile(filepath=BINANCE_API_KEYFILE) -> Credentials:
    """Load the Binance API keyfile"""

    if not os.path.exists(filepath):
        logger.warning(
            "The API keyfile {} was not found. Proceeding without authentication...".format(
                filepath
            )
        )

        return Credentials()

    else:
        with open(filepath, mode="r", encoding="utf-8") as fd:
            f = fd.readlines()

        return Credentials(key=f[0].strip(), secret=f[1].strip())


def save_api_keyfile(credentials: Credentials, filepath=BINANCE_API_KEYFILE):
    """Save the Binance API keyfile"""

    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with open(filepath, mode="wt", encoding="utf-8") as f:
        f.writelines([credentials.key + "\n", credentials.secret + "\n"])

    # TODO : wait for file creation (first time only) !
    return load_api_keyfile(
        filepath=filepath
    )  # return what we just saved, for verification.


if __name__ == "__main__":
    print(f"Keyfile: {BINANCE_API_KEYFILE}")
    f = load_api_keyfile()
    print(f"KEY : {f.get('key')}")
    print(f"SECRET : {f.get('secret')}")

import logging

import configparser

import os

# Resolve userpath to an absolute path

DEFAULT_BINANCE_API_KEYFILE = os.path.expanduser("~/.config/aiobinance/binance.key")

# If the environment variable is set, override the default value
BINANCE_API_KEYFILE = os.getenv("AIOBINANCE_API_KEYFILE", DEFAULT_BINANCE_API_KEYFILE)
BINANCE_API_KEYFILE = os.path.normpath(BINANCE_API_KEYFILE)

logger = logging.getLogger("aiobinance.config")


def load_api_keyfile():
    """Load the Binance API keyfile"""

    if not os.path.exists(BINANCE_API_KEYFILE):
        logger.warning("The API keyfile {} was not found!".format(BINANCE_API_KEYFILE))

    else:
        f = open(BINANCE_API_KEYFILE, encoding="utf-8").readlines()
        return {"key": f[0].strip(), "secret": f[1].strip()}


def save_api_keyfile(apikey, secret):
    """Save the Binance API keyfile"""

    if not os.path.exists(os.path.dirname(BINANCE_API_KEYFILE)):
        os.makedirs(os.path.dirname(BINANCE_API_KEYFILE))

    f = open(BINANCE_API_KEYFILE, mode="wt", encoding="utf-8")
    f.writelines([apikey + "\n", secret + "\n"])
    # TODO : wait for file creation (first time only) !
    return load_api_keyfile()  # return what we just saved for verification.


if __name__ == "__main__":
    print(f"Keyfile: {BINANCE_API_KEYFILE}")
    f = load_api_keyfile()
    print(f"KEY : {f.get('key')}")
    print(f"SECRET : {f.get('secret')}")

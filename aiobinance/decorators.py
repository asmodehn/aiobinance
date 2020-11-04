""" Useful decorators for this library, or its clients """
import inspect
from typing import Optional

from aiobinance.config import load_api_keyfile


def require_auth(mock_key: Optional[str] = None, mock_secret: Optional[str] = None):
    """
    >>> def wrapped_func(*args, **kwargs):
    ...     return args, kwargs
    >>> wrapped_func = require_auth(mock_key="key_mocked", mock_secret="secret_mocked")(wrapped_func)
    >>> wrapped_func()
    ((), {'key': 'key_mocked', 'secret': 'secret_mocked'})

    :param mock_key: a key if you dont want to use the user's environment to retrieve the apikey
    :param mock_secret: a secret if you dont want to use the user's environment to retrieve the secret
    If mock_key and mock_secret are not passed, instead hte user's apikey and secret will be passed in,
    from the configuration stored in his environment

    :return: a decorated python function.
    """
    def decorator(wrapped):

        def wrapper(*args, key: Optional[str] =None, secret: Optional[str] =None, **kwargs):

            # if key and secret are not passed
            if key is None or secret is None:
                if mock_key is None or mock_secret is None:
                    keystruct = load_api_keyfile()
                    key= keystruct.get('key'),
                    secret= keystruct.get('secret')
                else:
                    key =mock_key
                    secret = mock_secret
            return wrapped(*args, key=key, secret=secret, **kwargs)

        return wrapper
    return decorator


if __name__ == "__main__":
    import doctest
    doctest.testfile(__file__)

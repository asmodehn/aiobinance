import sys
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

import click

from aiobinance.config import (
    BINANCE_API_KEYFILE,
    Credentials,
    load_api_keyfile,
    save_api_keyfile,
)

# Ref : https://click.palletsprojects.com/en/7.x/complex/#interleaved-commands
pass_creds = click.make_pass_decorator(Credentials)


# TODO : https://github.com/tiangolo/typer


@click.group(invoke_without_command=True)
@click.option("--apikey", default=None)
@click.option("--secret", default=None)  # TODO : option to force anonymity
@click.option(
    "--store", default=False, is_flag=True
)  # TODO : maybe make this a command ??
@click.pass_context
def cli(ctx, apikey=None, secret=None, store=False):
    """ Managing user account """

    if apikey is not None and secret is not None:
        creds = Credentials(key=apikey, secret=secret)
    else:
        # tentative loading of the API key
        creds = load_api_keyfile()

        if creds.key is None:
            # no keyfile found
            print(f"{BINANCE_API_KEYFILE} Not Found !")
            # check for interactive terminal
            if hasattr(sys, "ps1"):
                print(
                    "- Interactive Terminal detected. Now Entering Binance APIkey and secret - "
                )
                apikey = input("APIkey: ")
                secret = input("secret: ")
                creds = Credentials(key=apikey, secret=secret)
            # else we assume the command doesnt require credentials

    if ctx.invoked_subcommand is None:
        # No subcommand invoke, just store the credentials
        if store:
            stored = save_api_keyfile(credentials=creds)
            assert stored == creds
            print(
                f"apikey and secret stored in {BINANCE_API_KEYFILE}.\nRemove it and re-run this command to replace it."
            )

        print(f"apikey: {creds}")

    # else:
    #     click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

    # print(creds)
    ctx.obj = creds


if __name__ == "__main__":
    cli()

from ptpython.repl import PythonRepl

import aiobinance


def configure_ptpython(repl: PythonRepl) -> None:
    # noop for now...
    return


async def embedded_ptpython():
    from ptpython.repl import embed, enable_deprecation_warnings

    enable_deprecation_warnings()
    return await embed(
        globals={**globals(), "aiobinance": aiobinance},
        locals=locals(),
        configure=configure_ptpython,
        title="aioBinance REPL",
        return_asyncio_coroutine=True,
    )


if __name__ == "__main__":
    # This module taken independently starts the repl, as an interactive test.
    # It is connected to the binance but without any authentication or configuration.
    # These could be done interactively however...
    import asyncio

    asyncio.run(embedded_ptpython(), debug=True)

import inspect
import io

import pytest

import aiobinance.repl


def test_configure_ptpython():
    from ptpython.repl import PythonRepl

    output = io.StringIO

    glbs = globals()
    lcls = locals()

    repl = PythonRepl(
        get_globals=lambda: glbs,
        get_locals=lambda: lcls,
        input=io.StringIO("aiobinance.__version__"),
    )
    aiobinance.repl.configure_ptpython(repl)

    assert "aiobinance" in repl.get_globals()
    assert aiobinance == repl.get_globals()["aiobinance"]

    # TODO : more test to verify repl configuration regarding accessible aiobinance commands


@pytest.mark.asyncio
async def test_embedded_repl():
    coro = aiobinance.repl.embedded_ptpython()
    assert inspect.iscoroutine(coro)
    # TODO : more tests to verify interaction with various terminal environments...


if __name__ == "__main__":
    pytest.main(["-s", __file__])

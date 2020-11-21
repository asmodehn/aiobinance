import inspect
import io

import pytest
from ptpython.completer import CompletePrivateAttributes
from ptpython.layout import CompletionVisualisation
from ptpython.repl import PythonRepl

import aiobinance.repl


def test_configure_ptpython():

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

    assert repl.complete_private_attributes == CompletePrivateAttributes.NEVER
    assert repl.completion_visualisation == CompletionVisualisation.POP_UP

    # TODO : more test to verify repl configuration regarding accessible aiobinance commands


@pytest.mark.asyncio
async def test_embedded_repl():
    coro = aiobinance.repl.embedded_ptpython()
    assert inspect.iscoroutine(coro)

    # TODO : more tests to verify interaction with various terminal environments...

    # because we cannot bring up a repl in test.
    # with pytest.raises(io.UnsupportedOperation):
    #     await coro
    # well turns out we can ?!?!


if __name__ == "__main__":
    pytest.main(["-s", __file__])

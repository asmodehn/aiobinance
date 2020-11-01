
import IPython


def embedded_repl():
    # What is visible in this context controls
    # what is directly visible & actionable via the REPL.

    import aiobinance

    return IPython.embed(

    )


if __name__ == "__main__":
    # This module taken independently starts the repl, as an interactive test.
    # It is connected to the binance but without any authentication or configuration.
    # These could be done interactively however...
    embedded_repl()

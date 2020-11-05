import IPython


def embedded_repl():
    # What is visible in this context controls
    # what is directly visible & actionable via the REPL.

    # First create a config object from the traitlets library
    from traitlets.config import Config

    c = Config()

    # Now we can set options as we would in a config file:
    #   c.Class.config_value = value
    # For example, we can set the exec_lines option of the InteractiveShellApp
    # class to run some code when the IPython REPL starts
    c.InteractiveShellApp.exec_lines = [
        'print("\\nimporting aiokraken...\\n")',
        "import aiokraken",
        "aiokraken",
    ]
    c.InteractiveShell.colors = "LightBG"
    c.InteractiveShell.confirm_exit = False
    c.TerminalIPythonApp.display_banner = False

    # TODO : %autoawait to easily run requests

    # Now we start ipython, embedded, with our configuration
    return IPython.embed(config=c)


if __name__ == "__main__":
    # This module taken independently starts the repl, as an interactive test.
    # It is connected to the binance but without any authentication or configuration.
    # These could be done interactively however...
    embedded_repl()

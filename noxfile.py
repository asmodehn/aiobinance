import subprocess

import nox

# Whenever type-hints are completed on a file it should be added here so that
# this file will continue to be checked by mypy. Errors from other files are
# ignored.
TYPED_FILES = {"aiobinance/api/__init__.py", "aiobinance/api/" "aiobinance/__init__.py"}
SOURCE_FILES = ["docs/", "aiobinance/", "tests/", "noxfile.py", "setup.py"]


# Ref : urllib3 has a strict nox-based process that we duplicate here.
@nox.session
def lint(session):
    # TODO : centralise tool versions... (pipfile + nox + precommit)
    session.install("flake8", "flake8-2020", "black==20.8b1", "isort==5.6.4", "mypy")
    session.run("flake8", "--version")
    session.run("black", "--version")
    session.run("isort", "--version")
    session.run("mypy", "--version")

    # TODO : centralise tool arguments... (nox + precommit)
    session.run("isort", "--profile", "black", "--check", *SOURCE_FILES)
    session.run("black", "--check", *SOURCE_FILES)
    session.run(
        "flake8",
        "--max-complexity=18",
        "--select=B,C,E,F,W,T4,B9",
        # these are errors that will be ignored by flake8
        # check out their meaning here
        # https://flake8.pycqa.org/en/latest/user/error-codes.html
        "--ignore=E203,E266,E501,W503,F403,F401,E402",
        *SOURCE_FILES
    )

    session.log("mypy --strict aiobinance")
    all_errors, errors = [], []
    process = subprocess.run(
        ["mypy", "--strict", "aiobinance"],
        env=session.env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Ensure that mypy itself ran successfully
    assert process.returncode in (0, 1)

    for line in process.stdout.split("\n"):
        all_errors.append(line)
        filepath = line.partition(":")[0]
        if filepath.replace(".pyi", ".py") in TYPED_FILES:
            errors.append(line)
    session.log("all errors count: {}".format(len(all_errors)))
    if errors:
        session.error("\n" + "\n".join(sorted(set(errors))))


@nox.session(python=["3.7", "3.8", "3.9"])
def tests(session):

    # install the package first to retrieve all dependencies before testing
    session.install(".")
    session.install("pytest", "pytest-recording", "pytest-asyncio")

    # displaying current machine date (it could influence tests if not handled properly)
    session.run(" date --iso-8601=ns".split())

    session.run("pytest", "-sv")

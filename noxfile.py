import subprocess

import nox

# Whenever type-hints are completed on a file it should be added here so that
# this file will continue to be checked by mypy. Errors from other files are
# ignored.
TYPED_FILES = {
    "aiobinance/api/__init__.py",
    "aiobinance/api/"
    "aiobinance/__init__.py",
}
SOURCE_FILES = [
    "docs/",
    "aiobinance/",
    "tests/",
    "noxfile.py",
    "setup.py",
]


# Ref : urllib3 has a strict nox-based process that we duplicate here.
@nox.session
def lint(session):
    session.install("flake8", "flake8-2020", "black", "isort", "mypy")
    session.run("flake8", "--version")
    session.run("black", "--version")
    session.run("isort", "--version")
    session.run("mypy", "--version")

    session.run("black", "--check", *SOURCE_FILES)
    session.run("isort", "--check", *SOURCE_FILES)
    session.run("flake8", *SOURCE_FILES)

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


@nox.session(python=['3.6', '3.7', '3.8'])
def tests(session):

    # install the package first to retrieve all dependencies before testing
    session.install(".")
    session.install('pytest', 'pytest-recording')

    session.run('pytest', '-s')

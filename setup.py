from setuptools import setup

setup(
    name="aiobinance",
    version="0.1",
    description="aiobinance",
    url="http://github.com/asmodehn/aiobinance",
    author="AlexV",
    author_email="asmodehn@gmail.com",
    license="GPLv3",
    packages=["aiobinance"],
    install_requires=[
        "pydantic",
        "pandas",
        "requests",
        "click",
        "ptpython",
        "jedi",
        "hypothesis",
        "bokeh",
        "tabulate",
        "result",
        "cached_property",  # todo : check py3.7 3.8 3.9 (from functools)
    ],
    zip_safe=False,
)

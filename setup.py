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
    install_requires=["pydantic", "pandas", "requests", "click", "ipython", "bokeh"],
    zip_safe=False,
)

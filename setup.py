import setuptools

__version__ = "0.0.1"

with open("README.txt") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="sgml",
    version=__version__,
    author="Nick Vollmar",
    author_email="nick.vollmar@gmail.com",
    description="Interpreter for the SGML 'language'",
    long_description=long_description,
    long_description_content_type="text/plain",
    url="https://big.horse",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

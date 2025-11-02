from setuptools import setup, find_packages

setup(
    name="stocksage",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # List your project dependencies here
        "fastapi",
        "uvicorn",
        # Add other dependencies as needed
    ],
)

from setuptools import setup, find_packages

setup(
    name="avaniko-ai",
    version="1.0.0",
    description="Official Python SDK for Avaniko AI Platform",
    author="Avaniko",
    author_email="dev@avaniko.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.27.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

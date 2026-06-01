"""
AOF CLI — pip install setup

Install in development mode (editable, no copy):
    pip install -e tools/

Install normally:
    pip install tools/

After installation the `aof` command is available system-wide:
    aof validate my-agent.yaml
    aof create my-payment-agent.yaml
    aof check my-agent.yaml
"""

from setuptools import setup

setup(
    name="aof-cli",
    version="1.0.0",
    description="CLI for the Agent Ownership Framework (AOF)",
    long_description=(
        "Command-line tool for validating, creating, and checking AOF v1 "
        "agent ownership contracts. Wraps the existing JSON Schema validator "
        "and adds a human-readable eight-boundary governance checklist."
    ),
    author="Anitha Jagadeesh",
    author_email="anithajagadeesh@gmail.com",
    url="https://github.com/ajwork-art/agent-ownership-framework",
    license="MIT",
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "jsonschema>=4.0",
    ],
    # scripts= installs the raw file as an executable on Unix/Mac and
    # generates a .exe + -script.py wrapper on Windows automatically.
    scripts=["aof"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Office/Business",
    ],
)

from typing import Tuple
import pytest
from pathlib import Path
from .utils import SnkCliRunner
from snk_cli.config import SnkConfig
from snk_cli import CLI
import yaml

@pytest.fixture()
def example_config():
    return Path("tests/data/config.yaml")


@pytest.fixture()
def local_runner():
    cli = CLI("tests/data/workflow")
    runner = SnkCliRunner(cli)
    return runner.invoke

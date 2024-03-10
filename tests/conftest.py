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

class Request:
    param: Tuple[dict, SnkConfig, str]

@pytest.fixture
def dynamic_runner(tmp_path_factory, request: Request) -> SnkCliRunner:
    """Create a CLI Runner from a SNK and config file"""
    path = Path(tmp_path_factory.mktemp("snk"))
    config, snk_config, snakefile_text = request.param
    path = Path(tmp_path_factory.mktemp("workflow"))
    snk_path = path / "snk.yaml"
    config_path = path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    snk_config.to_yaml(snk_path)
    snakefile_path = path / "Snakefile"
    snakefile_path.write_text(snakefile_text)
    cli = CLI(path)
    runner = SnkCliRunner(cli)
    return runner.invoke
import pytest
import yaml
from snk_cli.cli import CLI
from snk_cli.config import SnkConfig
from snk_cli.testing import SnkCliRunner
import tempfile
from pathlib import Path

def dynamic_runner(config: dict, snk_config: SnkConfig, snakefile_text="configfile: 'config.yaml'\nprint(config)", tmp_path=None) -> SnkCliRunner:
    """Create a CLI Runner from a SNK and config file"""
    if tmp_path is None:
        tmp_path = Path(tempfile.mkdtemp())
    snk_path = tmp_path / "snk.yaml"
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    snk_config.to_yaml(snk_path)
    snakefile_path = tmp_path / "Snakefile"
    snakefile_path.write_text(snakefile_text)
    cli = CLI(tmp_path, snk_config=snk_config)
    runner = SnkCliRunner(cli)
    return runner
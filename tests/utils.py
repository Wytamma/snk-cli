import pytest
from snk_cli.config import SnkConfig
from snk_cli.testing import SnkCliRunner


def gen_dynamic_runner_fixture(config: dict = dict, snk: SnkConfig = SnkConfig(), snakefile_text="configfile: 'config.yaml'\nprint(config)") -> SnkCliRunner:
    return pytest.mark.parametrize('dynamic_runner', [(config, snk, snakefile_text)], indirect=["dynamic_runner"])
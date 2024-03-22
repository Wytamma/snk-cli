from snk_cli.config import SnkConfig
from ..utils import dynamic_runner


def test_skip_missing(tmp_path):
    runner = dynamic_runner({"missing": True}, SnkConfig(skip_missing=True, cli={"visible": {"help": "visible"}}), tmp_path=tmp_path)
    res = runner.invoke(["run", "--help"])
    assert res.exit_code == 0, res.stderr
    assert "missing" not in res.stdout, res.stderr
    assert "visible" in res.stdout, res.stderr


def test_additional_snakemake_args(tmp_path):
    runner = dynamic_runner({"missing": True}, SnkConfig(additional_snakemake_args=["--help"]), tmp_path=tmp_path)
    res = runner.invoke(["run", "-v"])
    assert res.exit_code == 0, res.stderr
    assert "Snakemake is a Python based language and execution environment" in res.stdout, res.stderr


def test_snk_config_commands_run_only(tmp_path):
    runner = dynamic_runner({}, SnkConfig(commands=["run"]), tmp_path=tmp_path)
    res = runner.invoke(["--help"])
    assert res.exit_code == 0, res.stderr
    assert "run" in res.stdout, res.stderr
    assert "config" not in res.stdout, res.stderr
    assert "env" not in res.stdout, res.stderr
    assert "script" not in res.stdout, res.stderr
    assert "profile" not in res.stdout, res.stderr


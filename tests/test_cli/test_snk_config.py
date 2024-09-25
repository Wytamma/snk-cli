from snk_cli.config import SnkConfig
from ..utils import dynamic_runner
from pathlib import Path

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

def test_non_standard_snakefile(tmp_path):
    with open(tmp_path / "Snakefile2", "w") as f:
        f.write("print('Snakefile2')")
    runner = dynamic_runner({}, SnkConfig(snakefile=tmp_path / "Snakefile2"), tmp_path=tmp_path)
    res = runner.invoke(["run"])
    assert res.exit_code == 0, res.stderr
    assert "Snakefile2" in res.stdout, res.stderr

def test_non_standard_configfile(tmp_path):
    with open(tmp_path / "config2.yaml", "w") as f:
        f.write("value: config2")
    runner = dynamic_runner({}, SnkConfig(configfile=tmp_path / "config2.yaml"), tmp_path=tmp_path)
    res = runner.invoke(["run"])
    assert res.exit_code == 0, res.stderr
    assert "config2" in res.stdout, res.stderr

def test_snk_config_with_enums(tmp_path):
    runner = dynamic_runner({}, SnkConfig(cli={"test": {"choices": ["enum1", "enum2"], "type": "enum"}}), tmp_path=tmp_path)
    res = runner.invoke(["run", "--help"])
    assert res.exit_code == 0, res.stderr
    assert "enum1" in res.stdout, res.stderr
    assert "enum2" in res.stdout, res.stderr
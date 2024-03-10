from snk_cli.config import SnkConfig
from ..utils import gen_dynamic_runner_fixture, SnkCliRunner


@gen_dynamic_runner_fixture({"missing": True}, SnkConfig(skip_missing=True, cli={"visible": {"help": "visible"}}))
def test_skip_missing(dynamic_runner: SnkCliRunner):
    res = dynamic_runner(["run", "--help"])
    assert res.exit_code == 0, res.stderr
    assert "missing" not in res.stdout, res.stderr
    assert "visible" in res.stdout, res.stderr


@gen_dynamic_runner_fixture({"missing": True}, SnkConfig(additional_snakemake_args=["--help"]))
def test_additional_snakemake_args(dynamic_runner: SnkCliRunner):
    res = dynamic_runner(["run", "-v"])
    assert res.exit_code == 0, res.stderr
    assert "Snakemake is a Python based language and execution environment" in res.stdout, res.stderr
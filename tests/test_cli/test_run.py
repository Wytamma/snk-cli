from snk_cli.config.config import SnkConfig
from ..utils import SnkCliRunner, gen_dynamic_runner_fixture


def test_config_override(local_runner: SnkCliRunner):
    res = local_runner(
        [
            "run",
            "--text",
            "passed from the cli to overwrite config",
            "--config",
            "tests/data/workflow/config.yaml",
            "-f",
        ]
    )
    assert res.exit_code == 0, res.stderr
    assert "hello_world" in res.stderr
    assert "passed from the cli to overwrite config" in res.stdout


def test_exit_on_fail(local_runner: SnkCliRunner):
    res = local_runner(["run", "-f", "error"])
    assert res.exit_code == 1, res.stderr

@gen_dynamic_runner_fixture({"value": "config"}, SnkConfig(skip_missing=True, cli={"value": {"default": "snk"}}))
def test_run_with_config(dynamic_runner: SnkCliRunner):
    res = dynamic_runner(["run"])
    assert res.exit_code == 0, res.stderr
    assert "snk" in res.stdout
    res = dynamic_runner(["run", "--config", "tests/data/print_config/config.yaml"])
    assert res.exit_code == 0, res.stderr
    assert "config" in res.stdout
    res = dynamic_runner(["run", "--value", "cli"])
    assert res.exit_code == 0, res.stderr
    assert "cli" in res.stdout
    res = dynamic_runner(
        ["run", "-v", "--value", "cli", "--config", "tests/data/print_config/config.yaml",]
    )
    assert res.exit_code == 0, res.stderr
    assert "cli" in res.stdout, res.stderr

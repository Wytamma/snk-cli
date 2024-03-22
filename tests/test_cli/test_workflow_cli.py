from pathlib import Path
from snk_cli.utils import flatten, convert_key_to_snakemake_format
import snakemake
import pytest
from ..utils import SnkCliRunner


def test_flatten(example_config: Path):
    config = snakemake.load_configfile(example_config)
    flat_config = flatten(config)
    assert flat_config["diffexp:contrasts:A-vs-B"] == ["A", "B"]


@pytest.mark.parametrize(
    "key, value, expected",
    [
        ("a:b:c", 42, {"a": {"b": {"c": 42}}}),
        ("x:y:z", "hello", {"x": {"y": {"z": "hello"}}}),
        ("d:e", [1, 2, 3], {"d": {"e": [1, 2, 3]}}),
        ("h", "world", {"h": "world"}),
    ],
)
def test_convert_key_to_snakemake_format(key, value, expected):
    assert convert_key_to_snakemake_format(key, value) == expected


def test_help(local_runner: SnkCliRunner):
    res = local_runner(["--help"])
    assert res.exit_code == 0, res.stderr
    assert "Usage:" in res.stdout
    

def test_version(local_runner: SnkCliRunner):
    res = local_runner(["--version"])
    assert res.exit_code == 0, res.stderr
    assert "0.13.0" in res.stdout

def test_path(local_runner: SnkCliRunner):
    res = local_runner(["--path"])
    assert res.exit_code == 0, res.stderr
    assert "/workflow" in res.stdout

def test_profile(local_runner: SnkCliRunner):
    res = local_runner(["profile", "-h"])
    assert res.exit_code == 0, res.stderr
    assert "list" in res.stdout, res.stderr
    assert "show" in res.stdout, res.stderr

def test_info(local_runner: SnkCliRunner):
    res = local_runner(["info"])
    assert res.exit_code == 0, res.stderr
    assert "workflow" in res.stdout, res.stderr
    assert "version" in res.stdout
    assert "workflow_dir_path" in res.stdout

def test_config(local_runner: SnkCliRunner):
    res = local_runner(["config"])
    assert res.exit_code == 0, res.stderr
    assert "output: hello.txt" in res.stdout

def test_run_cli_help(local_runner: SnkCliRunner):
    res = local_runner(["run", "-h"])
    assert res.exit_code == 0, res.stderr
    assert "workflow" in res.stdout, res.stderr
    assert "times" in res.stdout
    assert "text" in res.stdout

@pytest.mark.parametrize("filetype", ["pdf", "svg", "png"])
def test_dag(local_runner: SnkCliRunner, tmp_path, filetype):
    args = ["run", "--dag", f"{tmp_path}/dag.{filetype}"]
    res = local_runner(args)
    assert res.exit_code == 0, res.stderr
    assert Path(f"{tmp_path}/dag.{filetype}").exists()


def test_hidden_option(local_runner: SnkCliRunner):
    res = local_runner(["run", "--help"])
    assert res.exit_code == 0, res.stderr
    assert "hidden" not in res.stdout, res.stdout
    assert "visible" in res.stdout, res.stdout


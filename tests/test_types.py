# integration tests for the annotation types from the snk config, snakemake config, and the command line interface

import pytest
from .utils import dynamic_runner
from snk_cli.config import SnkConfig


@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # str
    (
        {"example": "1"},
        {"example": {"type": "str"}},
        ["--example", "1"],
        "{'example': '1'}"
    )])
def test_str(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr
    
@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # int
    (
        {"example": "1"},
        {"example": {"type": "int"}},
        ["--example", "1"],
        "{'example': 1}"
    )])
def test_int(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # float
    (
        {"example": "1"},
        {"example": {"type": "float"}},
        ["--example", "1"],
        "{'example': 1.0}"
    )])
def test_float(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # bool
    (
        {"example": "1"},
        {"example": {"type": "bool"}},
        ["--example"],
        "{'example': True}"
    )])
def test_bool(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # path
    (
        {"example": "file"},
        {"example": {"type": "path"}},
        ["--example", "file"],
        "{'example': 'file'}"
    )])
def test_path(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # list
    (
        {"example": [1,2,3]},
        {"example": {"type": "list"}},
        ["--example", "1", "--example", "2", "--example", "3"],
        "{'example': ['1', '2', '3']}"
    )])
def test_list(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # pair
    (
        {"example": [1, 2]},
        {"example": {"type": "pair"}},
        ["--example", "1", "2"],
        "{'example': ['1', '2']}"
    ),
    (
        {"example": [1, 2]},
        {"example": {"type": "pair[int, int]"}},
        ["--example", "1", "2"],
        "{'example': [1, 2]}"
    ),
    (
        {"example": ["1", "2"]},
        {"example": {"type": "pair[float, float]"}},
        ["--example", "1", "2"],
        "{'example': [1.0, 2.0]}"
    ),
    (
        {"example": ["1", "2"]},
        {"example": {"type": "pair[str, str]"}},
        ["--example", "1", "2"],
        "{'example': ['1', '2']}"
    ),
    (
        {"example": ["1", "2"]},
        {"example": {"type": "pair[str, int]"}},
        ["--example", "1", "2"],
        "{'example': ['1', 2]}"
    ),
    (
        {"example": ["1", "2"]},
        {"example": {"type": "pair[int, str]"}},
        ["--example", "1", "2"],
        "{'example': [1, '2']}"
    )
])
def test_pair(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # choices
    (
        {"example": 1},
        {"example": {"type": "int", "choices": [1, 2, 3]}},
        ["--example", 1],
        "{'example': 1}"
    ),
    (
        {"example": 1},
        {"example": {"type": "int", "choices": [2, 3], "default": 2}},
        [],
        "{'example': 2}"
    ),
    ])
def test_choices(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr

@pytest.mark.parametrize("snakemake_config,annotations,cli_args,expected", [
    # dict
    (
        {"example": {"key": "value"}},
        {"example": {"type": "dict", "default": [["key", "value"]]}},
        [],
        "{'example': {'key': 'value'}}"
    ),
    (
        {"example": {"key": "value"}},
        {"example": {"type": "dict"}},
        [],
        "{'example': {'key': 'value'}}"
    ),
    (
        {"example": {"number": 1}},
        {"example": {"type": "dict[str, int]"}},
        [],
        "{'example': {'number': 1}}"
    ),
    (
        {},
        {"example": {"type": "dict[str, str]"}},
        ["--example", "new", "2"],
        "{'example': {'new': '2'}}"
    )
    ])
def test_dict(snakemake_config, annotations, cli_args, expected):
    snk_config = SnkConfig(cli=annotations)
    runner = dynamic_runner(snakemake_config, snk_config)
    res = runner.invoke(["run"] + cli_args)
    assert res.exit_code == 0, res.stderr
    assert expected in res.stdout, res.stderr
from snk_cli.conda import conda_environment_factory
from snakemake.deployment.conda import Env
from pathlib import Path


def test_conda_env(tmp_path):
    env = conda_environment_factory("tests/data/workflow/workflow/envs/wget.yml", tmp_path)
    assert isinstance(env, Env)
    assert not Path(env.address).exists()
    env.create()
    assert Path(env.address).exists()

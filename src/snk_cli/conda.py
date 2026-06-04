# This file contains functions to create and manage conda environments for snakemake workflows
# it needs to work with v7, v8, and v9 of snakemake
from pathlib import Path
from packaging import version
from types import SimpleNamespace
import inspect
import os

from snk_cli.utils import check_command_available
from snakemake.deployment.conda import Env
import snakemake

try:
    snakemake_version_text = snakemake.__version__
except AttributeError:
    from snakemake.common import __version__ as snakemake_version_text

snakemake_version = version.parse(snakemake_version_text)
is_snakemake_version_8_or_above = snakemake_version >= version.parse('8')
is_snakemake_version_9_or_above = snakemake_version >= version.parse('9')


def create_persistence_paths(conda_prefix):
    """
    Minimal workflow.persistence replacement for Env path calculation.
    """
    return SimpleNamespace(
        conda_env_path=Path(conda_prefix).resolve() if conda_prefix else None,
        _metadata_path=None,
        _incomplete_path=None,
        shadow_path=None,
        conda_env_archive_path=os.path.join(Path(".snakemake"), "conda-archive"),
        container_img_path=None,
        aux_path=None,
    )


def _create_workflow_namespace(conda_prefix):
    """
    Full duck-typed workflow mock for v9+, where Workflow.__init__ requires
    logger_manager — too complex to construct just for conda env management.
    Provides only the attributes that snakemake.deployment.conda.Env accesses.
    """
    persistence = create_persistence_paths(conda_prefix)
    return SimpleNamespace(
        persistence=persistence,
        deployment_settings=SimpleNamespace(apptainer_args=""),
        runtime_paths=[persistence.conda_env_path] if persistence.conda_env_path else [],
        sourcecache=SimpleNamespace(
            exists=lambda *a, **kw: False,
            open=lambda *a, **kw: None,
        ),
    )


def set_workflow_persistence(workflow, persistence):
    if hasattr(workflow, "_persistence"):
        workflow._persistence = persistence
    else:
        workflow.persistence = persistence


def get_frontend():
    if check_command_available("mamba"):
        return "mamba"
    return "conda"


def create_workflow_v7(conda_prefix):
    from snakemake.workflow import Workflow

    conda_frontend = get_frontend()
    workflow = Workflow(
        snakefile=Path(),
        overwrite_config=dict(),
        overwrite_workdir=None,
        overwrite_configfiles=[],
        overwrite_clusterconfig=dict(),
        conda_frontend=conda_frontend,
        use_conda=True,
    )
    set_workflow_persistence(workflow, create_persistence_paths(conda_prefix))
    return workflow


def create_workflow_v8(conda_prefix):
    from snakemake.api import (
        Workflow,
        ConfigSettings,
        DeploymentSettings,
        ResourceSettings,
        WorkflowSettings,
        StorageSettings,
    )

    # v9+ added logger_manager as a required param; simpler to mock the whole workflow
    if "logger_manager" in inspect.signature(Workflow).parameters:
        return _create_workflow_namespace(conda_prefix)

    conda_frontend = get_frontend()
    workflow = Workflow(
        config_settings=ConfigSettings(),
        resource_settings=ResourceSettings(),
        workflow_settings=WorkflowSettings(),
        storage_settings=StorageSettings(),
        deployment_settings=DeploymentSettings(
            conda_frontend=conda_frontend,
            conda_prefix=conda_prefix,
        ),
    )
    set_workflow_persistence(workflow, create_persistence_paths(conda_prefix))
    return workflow


def conda_environment_factory(env_file_path: Path, conda_prefix_dir_path: Path) -> Env:
    """
    Create a snakemake environment object from a given environment file and conda prefix directory.
    """
    if is_snakemake_version_8_or_above:
        snakemake_workflow = create_workflow_v8(conda_prefix_dir_path)
    else:
        snakemake_workflow = create_workflow_v7(conda_prefix_dir_path)
    env_file_path = Path(env_file_path).resolve()
    return Env(snakemake_workflow, env_file=env_file_path)

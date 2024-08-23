# This file contains functions to create and manage conda environments for snakemake workflows
# it needs to work with v 7 and 8 of snakemake
# 
from pathlib import Path
from packaging import version
from dataclasses import dataclass
import os

from snk_cli.utils import check_command_available
from snakemake.deployment.conda import Env
from snakemake.persistence import Persistence
import snakemake

snakemake_version = version.parse(snakemake.__version__)
is_snakemake_version_8_or_above = snakemake_version >= version.parse('8')

@dataclass
class PersistenceMock(Persistence):
    """
    Mock for workflow.persistence
    """
    conda_env_path: Path = None
    _metadata_path: Path = None
    _incomplete_path: Path = None
    shadow_path: Path = None
    conda_env_archive_path: Path = None
    container_img_path: Path = None
    aux_path: Path = None


def get_frontend():
    if check_command_available("mamba"):
        conda_frontend = "mamba"
    else:
        conda_frontend = "conda"
    return conda_frontend

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

    persistence = PersistenceMock(
        conda_env_path=Path(conda_prefix).resolve() if conda_prefix else None,
        conda_env_archive_path=os.path.join(Path(".snakemake"), "conda-archive"),
    )
    if hasattr(workflow, "_persistence"):
        workflow._persistence = persistence
    else:
        workflow.persistence = persistence
    return workflow

def create_workflow_v8(
        conda_prefix
    ):
    from snakemake.api import (
        Workflow,
        ConfigSettings,
        DeploymentSettings,
        ResourceSettings,
        WorkflowSettings,
        StorageSettings,
    )
    conda_frontend = get_frontend()
    workflow = Workflow(
        config_settings=ConfigSettings(),
        resource_settings=ResourceSettings(),
        workflow_settings=WorkflowSettings(),
        storage_settings=StorageSettings(),
        deployment_settings=DeploymentSettings(
            conda_frontend=conda_frontend, 
            conda_prefix=conda_prefix
        ),
    )
    persistence = PersistenceMock(
        conda_env_path=Path(conda_prefix).resolve() if conda_prefix else None,
        conda_env_archive_path=os.path.join(Path(".snakemake"), "conda-archive"),
    )
    if hasattr(workflow, "_persistence"):
        workflow._persistence = persistence
    else:
        workflow.persistence = persistence
    return workflow

def conda_environment_factory(env_file_path: Path, conda_prefix_dir_path: Path) -> Env:
    """
    Create a snakemake environment object from a given environment file and conda prefix directory
    """
    if is_snakemake_version_8_or_above:
        snakemake_workflow = create_workflow_v8(
            conda_prefix_dir_path
        )
    else:
        snakemake_workflow = create_workflow_v7(conda_prefix_dir_path)
    env_file_path = Path(env_file_path).resolve()
    env = Env(snakemake_workflow, env_file=env_file_path)
    return env

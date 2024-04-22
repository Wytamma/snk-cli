# This file contains functions to create and manage conda environments for snakemake workflows
# it needs to work with v 7 and 8 of snakemake
# 
from pathlib import Path
from packaging import version
from dataclasses import dataclass
import os

from snk_cli.utils import check_command_available
from snakemake.deployment.conda import Env
import snakemake

snakemake_version = version.parse(snakemake.__version__)


def create_workflow_v7(conda_prefix):
    
    if check_command_available("mamba"):
        conda_frontend = "mamba"
    else:
        conda_frontend = "conda"
    
    from snakemake.workflow import Workflow
    
    workflow = Workflow(
        snakefile=Path(),
        overwrite_config=dict(),
        overwrite_workdir=None,
        overwrite_configfiles=[],
        overwrite_clusterconfig=dict(),
        conda_frontend=conda_frontend,
        use_conda=True,
    )
    
    from snakemake.persistence import Persistence
    
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
        snakefile,
        config,
        configfiles,
        conda_prefix,
        workdir=None,
        config_args=None,
        use_conda=True,
    ):
    raise NotImplementedError("This function is not implemented yet")

def conda_environment_factory(env_file_path: Path, conda_prefix_dir_path: Path) -> Env:
    """
    Create a snakemake environment object from a given environment file and conda prefix directory
    """
    if snakemake_version >= version.parse('8'):
        snakemake_workflow = create_workflow_v8(
            conda_prefix_dir_path
        )
    else:
        snakemake_workflow = create_workflow_v7(conda_prefix_dir_path)
    env_file_path = Path(env_file_path).resolve()
    env = Env(snakemake_workflow, env_file=env_file_path)
    return env

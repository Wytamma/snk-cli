import os
import shutil
import subprocess
from pathlib import Path
import sys
from typing import List, Optional
import typer

from snk_cli.dynamic_typer import DynamicTyper
from snk_cli.conda import conda_environment_factory
from ..workflow import Workflow
from rich.console import Console
from rich.syntax import Syntax
from snakemake.deployment.conda import Conda, CreateCondaEnvironmentException

from concurrent.futures import ProcessPoolExecutor

def get_num_cores(default=4):
    try:
        return os.cpu_count()
    except:
        return default

def create_conda_environment_wrapper(args):
    """
    This wrapper is designed to be submitted to a ProcessPoolExecutor
    """
    env_path_str, conda_prefix_dir_str = args
    conda_prefix_dir = Path(conda_prefix_dir_str).resolve()
    env_path = Path(env_path_str).resolve()
    try:
        conda_environment_factory(env_path, conda_prefix_dir).create()
    except CreateCondaEnvironmentException as e:
        typer.secho(str(e), fg="red", err=True)
        return 1
    return 0


class EnvApp(DynamicTyper):
    def __init__(
        self,
        workflow: Workflow,
        conda_prefix_dir: Path,
    ):
        self.workflow = workflow
        self.conda_prefix_dir = conda_prefix_dir
        self.register_command(self.list, help="List the environments in the workflow.")
        self.register_command(self.show, help="Show the contents of an environment.")
        self.register_command(
            self.run, help="Run a command in one of the workflow environments."
        )
        self.register_command(
            self.activate, help="Activate a workflow conda environment."
        )
        self.register_command(self.remove, help="Remove conda environments.")
        self.register_command(self.create, help="Create conda environments.")

    def list(
        self,
        verbose: bool = typer.Option(
            False, "--verbose", "-v", help="Show conda paths."
        ),
    ):
        from rich.console import Console
        from rich.table import Table

        table = Table("Name", "CMD", "Env", show_header=True, show_lines=True)
        for env in self.workflow.environments:
            conda = conda_environment_factory(env, self.conda_prefix_dir)
            # address relative to cwd
            address = Path(conda.address)
            if address.exists():
                address = str(address) if verbose else f"[green]{address.name}[/green]"
                cmd = f"{self.workflow.name} env activate {env.stem}"
            else:
                address = ""
                cmd = f"{self.workflow.name} env create {env.stem}"
            table.add_row(
                env.stem, cmd, address
            )
        console = Console()
        console.print(table)

    def _get_conda_env_path(self, name: str) -> Path:
        env = [e for e in self.workflow.environments if e.stem == name]
        if not env:
            self.error(f"Environment {name} not found!")
        return env[0]

    def _shellcmd(self, env_address: str, cmd: str) -> str:
        if sys.platform.lower().startswith("win"):
            return Conda().shellcmd_win(env_address, cmd)
        return Conda().shellcmd(env_address, cmd)

    def show(
        self,
        name: str = typer.Argument(..., help="The name of the environment."),
        pretty: bool = typer.Option(
            False, "--pretty", "-p", help="Pretty print the environment."
        ),
    ):
        env_path = self._get_conda_env_path(name)
        env_file_text = env_path.read_text()
        if pretty:
            syntax = Syntax(env_file_text, "yaml")
            console = Console()
            console.print(syntax)
        else:
            self.echo(env_file_text)

    def run(
        self,
        name: str = typer.Argument(..., help="The name of the environment."),
        verbose: bool = typer.Option(
            False, "--verbose", "-v", help="Print the command to run."
        ),
        cmd: List[str] = typer.Argument(..., help="The command to run in environment."),
    ):
        env_path = self._get_conda_env_path(name)
        env = conda_environment_factory(env_path, self.conda_prefix_dir)
        env.create()
        cmd = self._shellcmd(env.address, " ".join(cmd))
        if verbose:
            self.log(cmd)
        user_shell = os.environ.get("SHELL", "/bin/bash")
        subprocess.run(cmd, shell=True, env=os.environ.copy(), executable=user_shell)

    def remove(
        self,
        name: Optional[str] = typer.Argument(None, help="The name of the environment. If not provided, all environments will be deleted."),
        force: bool = typer.Option(
            False, "--force", "-f", help="Force deletion of the environments."
        ),
    ):
        if name:
            env_path = self._get_conda_env_path(name)
            env = conda_environment_factory(env_path, self.conda_prefix_dir)
            path = Path(env.address)
            if not path.exists():
                self.error(f"Environment {name} not created!")
        else:
            path = self.conda_prefix_dir
        if force or input(f"Delete {path}? [y/N] ").lower() == "y":
            shutil.rmtree(path)
            self.success(f"Deleted {path}!")

    def create(
            self, 
            names: Optional[List[str]] = typer.Argument(None, help="The names of the environments to create. If not provided, all environments will be created."),
            max_workers: int = typer.Option(1, "--workers", "-w", help="Max number of envs to create in parallel.")
        ):
        if names:
            env_paths = [self._get_conda_env_path(name) for name in names]
        else:
            env_paths = self.workflow.environments
        env_args = [
            (
                path,
                self.conda_prefix_dir.resolve(),
            )
            for path in env_paths 
        ]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            status_codes = executor.map(create_conda_environment_wrapper, env_args)
        if any(status_codes):
            self.error("Failed to create all conda environments!")
        if names:
            self.success(f"Created environment{'s' if len(names) > 1 else ''} {' '.join(names)}!")
        else:
            self.success("All conda environments created!")

    def activate(
        self,
        name: str = typer.Argument(..., help="The name of the environment."),
        verbose: bool = typer.Option(
            False, "--verbose", "-v", help="Print the activation command."
        ),
    ):
        env_path = self._get_conda_env_path(name)
        self.log(f"Activating {name} environment... (type 'exit' to deactivate)")
        env = conda_environment_factory(env_path, self.conda_prefix_dir)
        env.create()
        user_shell = os.environ.get("SHELL", "/bin/bash")
        activate_cmd = self._shellcmd(env.address, user_shell)
        if verbose:
            self.log(activate_cmd)
        subprocess.run(activate_cmd, shell=True, env=os.environ.copy(), executable=user_shell)
        self.log(f"Exiting {name} environment...")

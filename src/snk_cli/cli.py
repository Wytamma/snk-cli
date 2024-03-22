import inspect
import platform

import typer
from pathlib import Path
from typing import Optional
import os


from snakemake import SNAKEFILE_CHOICES
from art import text2art

from snk_cli.dynamic_typer import DynamicTyper
from snk_cli.subcommands import EnvApp, ConfigApp, RunApp, ScriptApp, ProfileApp

from snk_cli.config.config import (
    SnkConfig,
    load_workflow_snakemake_config,
)
from snk_cli.options.utils import build_dynamic_cli_options
from snk_cli.workflow import Workflow


class CLI(DynamicTyper):
    """
    Constructor for the dynamic Snk CLI class.

    Args:
      workflow_dir_path (Path): Path to the workflow directory.

    Side Effects:
      Initializes the CLI class.

    Examples:
      >>> CLI(Path('/path/to/workflow'))
    """

    def __init__(self, workflow_dir_path: Path = None, *, pipeline_dir_path: Path = None, snk_config: SnkConfig = None) -> None:
        if pipeline_dir_path is not None:
            # raise a deprecation warning
            import warnings
            warnings.warn(
                "The `pipeline_dir_path` argument is deprecated and will be removed in a future release. Use `workflow_dir_path` instead.",
                DeprecationWarning,
            )
            workflow_dir_path = pipeline_dir_path
        if workflow_dir_path is None:
            # get the calling frame (the frame of the function that called this function)
            calling_frame = inspect.currentframe().f_back
            # get the file path from the calling frame
            workflow_dir_path = Path(calling_frame.f_globals["__file__"])
        else:
            workflow_dir_path = Path(workflow_dir_path)
        if workflow_dir_path.is_file():
            workflow_dir_path = workflow_dir_path.parent
        self.workflow = Workflow(path=workflow_dir_path)
        self.snakemake_config = load_workflow_snakemake_config(workflow_dir_path)
        if snk_config is None:
            self.snk_config = SnkConfig.from_workflow_dir(
                workflow_dir_path, create_if_not_exists=True
            )
        else:
            self.snk_config = snk_config
        if self.workflow.version:
            self.version = self.workflow.version
        else: 
            self.version = self.snk_config.version
        self.options = build_dynamic_cli_options(self.snakemake_config, self.snk_config)
        self.snakefile = self._find_snakefile()
        self.conda_prefix_dir = self.workflow.conda_prefix_dir
        self.singularity_prefix_dir = self.workflow.singularity_prefix_dir
        self.name = self.workflow.name
        self.verbose = False
        if (
            platform.system() == "Darwin"
            and platform.processor() == "arm"
            and not os.environ.get("CONDA_SUBDIR")
        ):
            os.environ["CONDA_SUBDIR"] = "osx-64"

        # dynamically create the logo
        self.logo = self._create_logo(
            tagline=self.snk_config.tagline, font=self.snk_config.font
        )
        callback = self._create_callback()
        callback.__doc__ = self.logo

        # registration
        self.register_callback(
            callback,
            invoke_without_command=True,
            context_settings={"help_option_names": ["-h", "--help"]},
        )

        # Subcommands
        if "info" in self.snk_config.commands:
            self.register_command(self.info, help="Show information about the workflow.")

        if "run" in self.snk_config.commands:
            run_app = RunApp(
                conda_prefix_dir=self.conda_prefix_dir,
                snk_config=self.snk_config,
                singularity_prefix_dir=self.singularity_prefix_dir,
                snakefile=self.snakefile,
                workflow=self.workflow,
                verbose=self.verbose,
                logo=self.logo,
                dynamic_run_options=self.options,
            )
            self.register_command(
                run_app,
                name="run",
            )
        if "config" in self.snk_config.commands:
            self.register_command(
                ConfigApp(
                    workflow=self.workflow,
                    options=self.options,
                ),
                name="config",
            )
        if self.workflow.environments and "env" in self.snk_config.commands:
            self.register_group(
                EnvApp(
                    workflow=self.workflow,
                    conda_prefix_dir=self.conda_prefix_dir,
                    snakemake_config=self.snakemake_config,
                    snakefile=self.snakefile,
                ),
                name="env",
                help="Access the workflow conda environments.",
            )
        if self.workflow.scripts and "script" in self.snk_config.commands:
            self.register_group(
                ScriptApp(
                    workflow=self.workflow,
                    conda_prefix_dir=self.conda_prefix_dir,
                    snakemake_config=self.snakemake_config,
                    snakefile=self.snakefile,
                ),
                name="script",
                help="Access the workflow scripts.",
            )
        if self.workflow.profiles and "profile" in self.snk_config.commands:
            self.register_group(
                ProfileApp(
                    workflow=self.workflow,
                ),
                name="profile",
                help="Access the workflow profiles.",
            )

    def _print_pipline_version(self, ctx: typer.Context, value: bool):
        if value:
            typer.echo(self.version)
            raise typer.Exit()

    def _print_pipline_path(self, ctx: typer.Context, value: bool):
        if value:
            typer.echo(self.workflow.path)
            raise typer.Exit()

    def _create_callback(self):
        def callback(
            ctx: typer.Context,
            version: Optional[bool] = typer.Option(
                None,
                "-v",
                "--version",
                help="Show the workflow version and exit.",
                is_eager=True,
                callback=self._print_pipline_version,
                show_default=False,
            ),
            path: Optional[bool] = typer.Option(
                None,
                "-p",
                "--path",
                help="Show the workflow path and exit.",
                is_eager=True,
                callback=self._print_pipline_path,
                show_default=False,
            ),
        ):
            if ctx.invoked_subcommand is None:
                typer.echo(f"{ctx.get_help()}")

        return callback

    def _create_logo(
        self, tagline="A Snakemake workflow CLI generated with snk", font="small"
    ):
        """
        Create a logo for the CLI.

        Args:
          tagline (str, optional): The tagline to include in the logo. Defaults to "A Snakemake workflow CLI generated with snk".
          font (str, optional): The font to use for the logo. Defaults to "small".

        Returns:
          str: The logo.

        Examples:
          >>> CLI._create_logo()
        """
        if self.snk_config.art:
            art = self.snk_config.art
        else:
            logo = self.snk_config.logo if self.snk_config.logo else self.name
            art = text2art(logo, font=font)
        doc = f"""\b{art}\b{tagline}"""
        return doc

    def _find_snakefile(self):
        """
        Search possible snakefile locations.

        Returns:
          Path: The path to the snakefile.

        Raises:
          FileNotFoundError: If the snakefile is not found.

        Examples:
          >>> CLI._find_snakefile()
        """
        for path in SNAKEFILE_CHOICES:
            if (self.workflow.path / path).exists():
                return self.workflow.path / path
        raise FileNotFoundError("Snakefile not found!")

    def info(self):
        """
        Display information about current workflow install.

        Returns:
          str: A JSON string containing information about the current workflow install.

        Examples:
          >>> CLI.info()
        """
        import json

        info_dict = {}
        info_dict["name"] = self.workflow.path.name
        info_dict["version"] = self.version
        info_dict["workflow_dir_path"] = str(self.workflow.path)
        typer.echo(json.dumps(info_dict, indent=2))


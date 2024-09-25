import typer
from snk_cli.dynamic_typer import DynamicTyper
from ..workflow import Workflow
from rich.console import Console
from rich.syntax import Syntax
from pathlib import Path


class ProfileApp(DynamicTyper):
    def __init__(
        self,
        workflow: Workflow,
    ):
        self.workflow = workflow
        self.register_command(self.list, help="List the profiles in the workflow.")
        self.register_command(self.show, help="Show the contents of a profile.")
        self.register_command(self.edit, help="Edit the contents of a profile.")

    def list(
        self,
        verbose: bool = typer.Option(
            False, "--verbose", "-v", help="Show profiles as paths."
        ),
    ):
        from rich.console import Console
        from rich.table import Table

        table = Table("Name", "CMD", show_header=True, show_lines=True)
        if verbose:
            table.add_column("Path")
        for profile in self.workflow.profiles:
            if verbose:
                path = str(profile.resolve())
                table.add_row(
                    profile.stem,
                    f"{self.workflow.name} profile show {profile.stem}",
                    path,
                )
            else:
                table.add_row(
                    profile.stem, f"{self.workflow.name} profile show {profile.stem}"
                )
        console = Console()
        console.print(table)

    def _get_profile_path(self, name: str) -> Path:
        profile = [
            p for p in self.workflow.profiles if p.name == name or p.stem == name
        ]
        if not profile:
            self.error(f"Profile {name} not found!")
        return profile[0] / "config.yaml"

    def show(
        self,
        name: str = typer.Argument(..., help="The name of the profile."),
        pretty: bool = typer.Option(
            False, "--pretty", "-p", help="Pretty print the profile."
        ),
    ):
        profile_path = self._get_profile_path(name)
        profile_file_text = profile_path.read_text()
        if pretty:
            syntax = Syntax(profile_file_text, "yaml")
            console = Console()
            console.print(syntax)
        else:
            typer.echo(profile_file_text)

    def _open_text_editor(self, file_path):
        """
        Opens the system's default text editor to edit the specified file.

        Parameters:
        file_path (str): The path to the file to be edited.
        """
        import subprocess
        import os
        import platform

        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(("open", file_path))
        else:  # Linux and other Unix-like systems
            editors = ["nano", "vim", "vi"]
            editor = None
            for e in editors:
                if (
                    subprocess.call(
                        ["which", e], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    == 0
                ):
                    editor = e
                    break
            if editor:
                subprocess.call([editor, file_path])
            else:
                self.error(
                    "No suitable text editor found. Please install nano or vim."
                )

    def edit(self, name: str = typer.Argument(..., help="The name of the profile.")):
        profile_path = self._get_profile_path(name)
        ## open the profile in the system editor
        self._open_text_editor(profile_path)

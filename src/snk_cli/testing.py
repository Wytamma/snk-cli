from typer.testing import CliRunner, Result
from dataclasses import dataclass
from typing import List
from snk_cli import CLI
import sys

@dataclass
class SnkCliRunner:
    """
    Dynamically creates a CLI Runner for testing.

    Args:
      cli (CLI): The CLI object to be tested.

    Attributes:
      runner (CliRunner): The CliRunner object used for testing.
    """

    cli: CLI
    runner = CliRunner(mix_stderr=False)

    def invoke(self, args: List[str]) -> Result:
        old_argv = sys.argv
        sys.argv = ['cli'] + args  # ensure that the CLI is invoked with the correct arguments
        result = self.runner.invoke(self.cli.app, args)
        sys.argv = old_argv
        return result
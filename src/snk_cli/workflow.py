from pathlib import Path
import sys
from typing import Optional
import importlib.util
import os

class Workflow:
    """
    Represents a workflow.

    Attributes:
      path (Path): The path to the workflow.
      repo (Repo): The git repository of the workflow.
      name (str): The name of the workflow.
    """

    def __init__(self, path: Path) -> None:
        """
        Initializes a Workflow object.

        Args:
          path (Path): The path to the workflow.

        Returns:
          None

        Notes:
          Initializes the `repo` and `name` attributes.
        """
        self.path = path
        self.editable = self.check_is_editable()
        self.name = self.path.name

    @property
    def executable(self):
        """
        Gets the executable of the workflow.

        Returns:
          Path: The path to the workflow executable.
        """
        workflow_bin_dir = self.path.parent.parent / "bin"
        name = self.name
        if sys.platform.startswith("win"):
            name += ".exe"
        return workflow_bin_dir / name
    
    @property
    def conda_prefix_dir(self):
        """
        Gets the conda prefix directory of the workflow. If in editable mode, the conda prefix directory is located in the .snakemake directory. Otherwise, it is located in the .conda directory in the workflow directory.

        Returns:
          Path: The path to the conda prefix directory.
        """
        return Path(".snakemake") / "conda" if self.editable else self.path / ".conda"

    @property
    def singularity_prefix_dir(self):
        """
        Gets the singularity prefix directory of the workflow.

        Returns:
          Path: The path to the singularity prefix directory.
        """
        if " " in str(self.path):
            # sigh, snakemake singularity does not support spaces in the path
            # https://github.com/snakemake/snakemake/blob/2ecb21ba04088b9e6850447760f713784cf8b775/snakemake/deployment/singularity.py#L130C1-L131C1
            return None
        return Path(".snakemake") / "singularity" if self.editable else self.path / ".singularity"
    
    def _is_editable_pip_install(self):
        # This function now acts as a method within the Workflow class
        package_spec = importlib.util.find_spec(self.name)
        if package_spec is None:
            return False  # Package is not installed

        package_location = package_spec.origin
        site_packages_paths = [p for p in sys.path if 'site-packages' in p]
        is_inside_site_packages = any(package_location.startswith(sp) for sp in site_packages_paths)

        if not is_inside_site_packages:
            return True

        for sp in site_packages_paths:
            egg_link_path = os.path.join(sp, self.name + '.egg-link')
            if os.path.isfile(egg_link_path):
                return True

        return False

    def check_is_editable(self):
        """
        Is the workflow editable?

        Returns:
          bool: True if the workflow is editable, False otherwise.
        """
        if self.path.is_symlink():
            return True
        try:
            return self._is_editable_pip_install()
        except Exception:
            return False

    def _find_folder(self, name) -> Optional[Path]:
        """
        Search for folder.

        Args:
          name: The name of the folder to search for.

        Returns:
          Optional[Path]: The path to the folder, or None if the folder is not found.
        """
        if (self.path / "workflow" / name).exists():
            return self.path / "workflow" / name
        if (self.path / name).exists():
            return self.path / name
        return None

    @property
    def profiles(self):
        workflow_profile_dir = self._find_folder("profiles")
        if workflow_profile_dir:
            return [p for p in workflow_profile_dir.glob("*") if p.is_dir() and (p / "config.yaml").exists()]
        return []

    @property
    def environments(self):
        workflow_environments_dir = self._find_folder("envs")
        if workflow_environments_dir:
            return [e for e in workflow_environments_dir.glob("*.yaml")] + [
                e for e in workflow_environments_dir.glob("*.yml")
            ]
        return []

    @property
    def scripts(self):
        workflow_environments_dir = self._find_folder("scripts")
        if workflow_environments_dir:
            return [s for s in workflow_environments_dir.iterdir() if s.is_file()]
        return []

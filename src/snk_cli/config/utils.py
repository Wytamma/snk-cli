from pathlib import Path
from snakemake import load_configfile

def get_version_from_config(config_path: Path, config_dict: dict = None) -> str:
    """
    Get the version from the config file or config dictionary.

    Args:
      config_path (Path): Path to the config file.
      config_dict (dict, optional): Config dictionary. Defaults to None.

    Returns:
      str: The version.

    Raises:
      FileNotFoundError: If the version file (__about__.py) is not found.
      KeyError: If the __version__ key is not found in the version file.

    Examples:
      >>> get_version_from_config(Path("config.yaml"))
      '0.1.0'
      >>> get_version_from_config(Path("config.yaml"), {"version": "0.2.0"})
      '0.2.0'
    """
    if not config_dict:
        config_dict = load_configfile(config_path)
    
    if "version" not in config_dict:
        return None 
    if config_dict["version"] is None:
        return None
    version = str(config_dict["version"])
    if "__about__.py" in version:
        # load version from __about__.py
        about_path = config_path.parent / version
        if not about_path.exists():
            raise FileNotFoundError(
                f"Could not find version file: {about_path}"
            )
        about = {}
        exec(about_path.read_text(), about)
        try:
            version = about["__version__"]
        except KeyError as e:
            raise KeyError(
                f"Could not find __version__ in file: {about_path}"
            ) from e
    return version
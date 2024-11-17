from typing import List, Tuple, get_origin
from ..config.config import SnkConfig
from ..utils import get_default_type, flatten
from .option import Option
from pathlib import Path
from enum import Enum

types = {
    "int": int,
    "integer": int,
    "float": float,
    "str": str,
    "string": str,
    "path": Path,
    "bool": bool,
    "boolean": bool,
    "list": List[str],
    "list[str]": List[str],
    "list[path]": List[Path],
    "list[int]": List[int],
    "list[float]": List[float],
    "pair": Tuple[str, str],
    "dict": dict,
    "dict[str, str]": dict[str, str],
    "dict[str, int]": dict[str, int],
}

# Define the basic types for the combinations
basic_types = [int, str, bool, float]

# Add the combinations of the basic types to the `types` dictionary
for t1 in basic_types:
    for t2 in basic_types:
        types[f"pair[{t1.__name__}, {t2.__name__}]"] = Tuple[t1, t2]

def get_keys_from_annotation(annotations):
    # Get the unique keys from the annotations
    # preserving the order
    keys = []
    for key in annotations:
        key = ":".join(key.split(":")[:-1])
        if key not in keys:
            keys.append(key)
    return keys

def create_option_from_annotation(
    annotation_key: str,
    annotation_values: dict,
    default_values: dict,
    from_annotation: bool = False,
) -> Option:
    """
    Create an Option object from a given annotation.

    Args:
      annotation_key (str): The key in the annotations.
      annotation_values (dict): The dictionary of annotation values.
      default_values (dict): Default value from config.
      from_annotation (bool, optional): Whether the option is from an annotation. Defaults to False.

    Returns:
      Option: An Option object.
    """
    config_default = default_values.get(annotation_key, None)
    default = annotation_values.get(f"{annotation_key}:default", config_default)
    updated = False
    if config_default is None or default != config_default:
        updated = True
    annotation_type = annotation_values.get(f"{annotation_key}:type", None) 
    if annotation_type is not None: 
        assert annotation_type in types, f"Type '{annotation_type}' not supported."
    annotation_type = annotation_type or get_default_type(default)
    annotation_type = types.get(
        annotation_type, List[str] if "list" in annotation_type else str
    )
    name = annotation_values.get(
        f"{annotation_key}:name", annotation_key.replace(":", "_")
    ).replace("-", "_")
    short = annotation_values.get(f"{annotation_key}:short", None)
    hidden = annotation_values.get(f"{annotation_key}:hidden", False)
    default=annotation_values.get(f"{annotation_key}:default", default)
    if default and get_origin(annotation_type) is tuple:
        assert len(default) == 2, f"Default value ({default}) for '{annotation_key}' should be a list of length 2."
    choices = annotation_values.get(f"{annotation_key}:choices", None)
    if choices:
        assert isinstance(choices, list), f"Choices should be a list for '{annotation_key}'."
    return Option(
        name=name,
        original_key=annotation_key,
        default=default,
        updated=updated,
        help=annotation_values.get(f"{annotation_key}:help", ""),
        type=annotation_type,
        required=annotation_values.get(f"{annotation_key}:required", False),
        short=short,
        flag=f"--{name.replace('_', '-')}",
        short_flag=f"-{short}" if short else None,
        hidden=hidden,
        from_annotation=from_annotation,
        choices=annotation_values.get(f"{annotation_key}:choices", None),
    )


def build_dynamic_cli_options(
    snakemake_config: dict, snk_config: SnkConfig
) -> List[dict]:
    """
    Builds a list of options from a snakemake config and a snk config.

    Args:
      snakemake_config (dict): A snakemake config.
      snk_config (SnkConfig): A snk config.

    Returns:
      List[dict]: A list of options.
    """
    flat_annotations = flatten(snk_config.cli)
    annotation_keys = get_keys_from_annotation(flat_annotations)
    flat_config = flatten(snakemake_config, stop_at=annotation_keys)
    options = {}

    # For every parameter in the config, create an option from the corresponding annotation
    for parameter in flat_config:
        if parameter not in annotation_keys and snk_config.skip_missing:
            continue
        options[parameter] = create_option_from_annotation(
            parameter,
            flat_annotations,
            default_values=flat_config,
        )

    # For every annotation not in config, create an option with default values    
    for key in annotation_keys:
        if key not in options:
            # in annotation but not in config
            options[key] = create_option_from_annotation(
                key,
                flat_annotations,
                default_values={},
                from_annotation=True,
            )
    return list(options.values())

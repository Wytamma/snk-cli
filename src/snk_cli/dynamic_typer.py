import typer
from typing import List, Callable
from inspect import signature, Parameter
from makefun import with_signature

from .options import Option
import sys


class DynamicTyper:
    app: typer.Typer

    def __init__(self):
        self.app = typer.Typer()

    def __call__(self):
        """
        Invoke the CLI.

        Side Effects:
          Invokes the CLI.

        Examples:
          >>> CLI(Path('/path/to/workflow'))()
        """
        self.app()

    def _set_app(self):
        """
        Set the app attribute.

        Side Effects:
          Sets the app attribute to a Typer object.
        """
        if not hasattr(self, "app"):
          self.app = typer.Typer()

    def register_default_command(self, command: Callable, **command_kwargs) -> None:
        """
        Register a default command to the CLI.

        Args:
          command (Callable): The command to register.

        Side Effects:
          Registers the command to the CLI.

        Examples:
          >>> CLI.register_default_command(my_command)
        """
        from makefun import with_signature
        from inspect import signature, Parameter

        command_signature = signature(command)
        params = list(command_signature.parameters.values())
        has_ctx = any([p.name == "ctx" for p in params])
        if not has_ctx:
            params.insert(
                0,
                Parameter(
                    "ctx",
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=typer.Context,
                ),
            )
            command_signature = command_signature.replace(parameters=params)

        @with_signature(command_signature)
        def wrapper(ctx: typer.Context, *args, **kwargs):
            if ctx.invoked_subcommand is None:
                if has_ctx:
                    return command(ctx, *args, **kwargs)
                return command(*args, **kwargs)

        self.register_callback(wrapper, invoke_without_command=True, **command_kwargs)

    def register_command(
        self, command: Callable, dynamic_options=None, **command_kwargs
    ) -> None:
        """
        Register a command to the CLI.

        Args:
          command (Callable): The command to register.
          dynamic_options (List[Option], optional): A list of dynamic options to add to the command.

        Side Effects:
          Registers the command to the CLI.

        Examples:
          >>> CLI.register_command(my_command)
          >>> CLI.register_command(my_command, dynamic_options=[option1, option2])
        """
        self._set_app()
        if dynamic_options is not None:
            command = self.add_dynamic_options(command, dynamic_options)
        if isinstance(command, DynamicTyper):
            self.app.registered_commands.extend(command.app.registered_commands)
        else:
            self.app.command(**command_kwargs)(command)

    def register_callback(self, command: Callable, **command_kwargs) -> None:
        """
        Register a callback to the CLI.

        Args:
          command (Callable): The callback to register.

        Side Effects:
          Registers the callback to the CLI.

        Examples:
          >>> CLI.register_callback(my_callback)
        """
        self._set_app()
        self.app.callback(**command_kwargs)(command)

    def register_group(self, group: "DynamicTyper", **command_kwargs) -> None:
        """
        Register a subcommand group to the CLI.

        Args:
          group (DynamicTyper): The subcommand group to register.

        Side Effects:
          Registers the subcommand group to the CLI.

        Examples:
          >>> CLI.register_group(my_group)
        """
        self._set_app()
        self.app.add_typer(group.app, **command_kwargs)

    def _create_cli_parameter(self, option: Option):
        """
        Creates a parameter for a CLI option.

        Args:
          option (Option): An Option object containing the option's name, type, required status, default value, and help message.

        Returns:
          Parameter: A parameter object for the CLI option.

        Examples:
          >>> option = Option(name='foo', type='int', required=True, default=0, help='A number')
          >>> create_cli_parameter(option)
          Parameter('foo', kind=Parameter.POSITIONAL_OR_KEYWORD, default=typer.Option(..., help='[CONFIG] A number'), annotation=int)
        """
        return Parameter(
            option.name,
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            default=typer.Option(
                ... if option.required else option.default,
                *[option.flag, option.short_flag] if option.short else [],
                help=f"{option.help}",
                rich_help_panel="Workflow Configuration",
                hidden=option.hidden,
            ),
            annotation=option.type,
        )

    def check_if_option_passed_via_command_line(self, option: Option):
        """
        Check if an option is passed via the command line.

        Args:
          option (Option): An Option object containing the option's name, type, required status, default value, and help message.

        Returns:
          bool: Whether the option is passed via the command line.
        """
        if option.flag in sys.argv:
            return True
        elif option.type is bool and f"--no-{option.flag[2:]}" in sys.argv:
            # Check for boolean flags like --foo/--no-foo
            return True
        elif option.short and option.short_flag in sys.argv:
            return True
        return False

    def add_dynamic_options(self, func: Callable, options: List[Option]):
        """
        Function to add dynamic options to a command.

        Args:
          func (Callable): The command to which the dynamic options should be added.
          options (List[Option]): A list of Option objects containing the options to add.

        Returns:
          Callable: A function with the dynamic options added.

        Examples:
          >>> my_func = add_dynamic_options_to_function(my_func, [option1, option2])
          >>> my_func
        """
        func_sig = signature(func)
        params = list(func_sig.parameters.values())
        for op in options[::-1]:
            params.insert(1, self._create_cli_parameter(op))
        new_sig = func_sig.replace(parameters=params)

        @with_signature(func_signature=new_sig, func_name=func.__name__)
        def func_wrapper(*args, **kwargs):
            """
            Wraps a function with dynamic options.

            Args:
              *args: Variable length argument list.
              **kwargs: Arbitrary keyword arguments.

            Returns:
              Callable: A wrapped function with the dynamic options added.

            Notes:
              This function is used in the `add_dynamic_options_to_function` function.
            """
            flat_config = None

            if kwargs.get("configfile"):
                from snakemake import load_configfile
                from .utils import flatten

                snakemake_config = load_configfile(kwargs["configfile"])
                flat_config = flatten(snakemake_config)

            for snk_cli_option in options:

                def add_option_to_args():
                    kwargs["ctx"].args.extend([f"--{snk_cli_option.name}", kwargs[snk_cli_option.name]])

                passed_via_command_line = self.check_if_option_passed_via_command_line(
                    snk_cli_option
                )

                if flat_config is None:
                    # If no config file is provided then all options should be added to the arguments
                    # later on we will check to see if they differ from any defaults
                    add_option_to_args()
                elif passed_via_command_line:
                    # If an option is passed via the command line if should override the default
                    add_option_to_args()
                elif flat_config and snk_cli_option.original_key not in flat_config:
                    # If a config file is provided and the snk_cli_option key isn't in it, 
                    # add the snk_cli_option to the arguments
                    add_option_to_args()

            kwargs = {
                k: v for k, v in kwargs.items() if k in func_sig.parameters.keys()
            }
            return func(*args, **kwargs)

        return func_wrapper

    def error(self, msg, exit=True):
        """
        Logs an error message (red) and exits (optional).

        Args:
          msg (str): The error message to log.
          exit (bool): Whether to exit after logging the error message.
        """
        typer.secho(msg, fg="red", err=True)
        if exit:
            raise typer.Exit(1)

    def success(self, msg):
        """
        Logs a success message (green).

        Args:
          msg (str): The success message to log.
        """
        typer.secho(msg, fg="green")

    def log(self, msg, color="yellow", stderr=True):
        """
        Logs a message (yellow).

        Args:
          msg (str): The message to log.
          color (str, optional): The color of the log message. Defaults to "yellow".
          stderr (bool, optional): Whether to log the message to stderr. Defaults to True.
        """
        typer.secho(msg, fg=color, err=stderr)

    def echo(self, msg):
        """
        Prints a message.

        Args:
          msg (str): The message to print.
        """
        typer.echo(msg)

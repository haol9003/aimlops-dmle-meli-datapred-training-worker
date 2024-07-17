from jsonargparse import CLI


class MainCLI:
    """Main CLI class to parse the arguments to run the commands.

    Add your custom commands here as new instance methods:

    ```python
    class MainCLI:
        def my_command(self, arg1: int, arg2: str = "default") -> None:
            # The logic to run my_command with arg1 and arg2:
            # python -m {{ package_import_name }}.{{ pipeline_name }}.cli my_command arg1 arg2
            print(f"arg1: {arg1}, arg2: {arg2}")
    ```
    """

    def __init__(self):
        """Initialize the CLI."""


def main():
    """This function parses the arguments to run the commands."""
    CLI(components=MainCLI)

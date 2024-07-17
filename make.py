#!/usr/bin/python3
from __future__ import annotations

import getpass
import inspect
import os
import platform
import shutil
import subprocess
import sys
from argparse import REMAINDER, ArgumentParser
from pathlib import Path

DEFAULT_VCS_VERSION = "0.0.1"

task_registry = {}


def register_task(func):
    """Registers a task in the task registry."""
    func_name = func.__name__.replace("_", "-")
    task_registry[func_name] = func
    return func


def get_compose_project_name(ssh: bool) -> str:
    """Gets the compose project name based on the current environment variables."""
    user_name = os.environ["COMPOSE_USER_NAME"]
    project_name = Path(__file__).parent.name
    platform = os.environ["COMPOSE_PLATFORM"]
    if ssh:
        ssh_port = os.environ["COMPOSE_SSH_PORT"]
        return f"{user_name}-{ssh_port}-{project_name}-{platform}"
    return f"{user_name}-{project_name}-{platform}"


def run_cmd(
    cmd: str | list,
    cwd: Path | None = None,
    capture_output: bool = True,
) -> str | None:
    """Runs a command in the shell and returns the output.

    Args:
        cmd: The command to run.
        cwd: The working directory to run the command in.
        capture_output: Whether to capture the output of the command.

    Returns:
        The output of the command if `capture_output` is `True`. None otherwise.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    if isinstance(cmd, list):
        # subprocess.run command requires a string when running through a shell
        cmd = " ".join([f'"{s}"' for s in cmd])
    try:
        print(f"Running command: {cmd}")
        process = subprocess.run(
            args=cmd,
            cwd=cwd or Path(__file__).parent,
            check=True,
            shell=True,
            encoding=sys.stdout.encoding,
            capture_output=capture_output,
        )
    except subprocess.CalledProcessError as error:
        if capture_output:
            print(error.stdout)
            print(error.stderr)
        raise error
    return process.stdout.strip() if capture_output else None


def docker_compose_cli() -> list[str]:
    """Gets the docker-compose CLI command."""
    docker_cmd = shutil.which("docker")
    if docker_cmd:
        # Try to use compose as a plugin
        docker_compose_cmd = [docker_cmd, "compose"]
        try:
            run_cmd(docker_compose_cmd)
            return docker_compose_cmd
        except subprocess.CalledProcessError as error:
            print("docker compose plugin is not available.")
            print("Falling back to docker-compose command.")

    docker_compose_cmd = shutil.which("docker-compose")
    if not docker_compose_cmd:
        raise RuntimeError("docker-compose is not installed in the host.")

    return [docker_compose_cmd]


def git_cli():
    """Gets the git CLI command."""
    cmd = shutil.which("git")
    if cmd is None:
        raise ValueError("git is not installed.")
    return cmd


def az_cli_cmd(az_cli_version: str = "2.54.0") -> list[str]:
    """Gets the Azure CLI command."""
    az_cli_version = os.environ.get("AZ_CLI_VERSION", az_cli_version)
    user_uid = os.environ["COMPOSE_USER_UID"]
    user_gid = os.environ["COMPOSE_USER_GID"]
    user_name = os.environ["COMPOSE_USER_NAME"]
    home_dir = os.environ["COMPOSE_HOME_DIR"]
    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{user_uid}:{user_gid}",
        "-e",
        f"HOME=/home/{user_name}",
        "-v",
        f"{home_dir}/{user_name}:/home/{user_name}",
        f"mcr.microsoft.com/azure-cli:{az_cli_version}",
        "az",
    ]
    return cmd


def get_project_version() -> str:
    """Gets the current version of this project from the VCS.

    Returns:
        The VCS version of the repository or DEFAULT_VCS_VERSION if not found.
    """
    try:
        tags = run_cmd([git_cli(), "rev-list", "--tags", "--max-count=1"])
        version = run_cmd([git_cli(), "describe", "--tags", tags])
        return version or DEFAULT_VCS_VERSION
    except subprocess.CalledProcessError:
        print(
            f"Could not get the project version from git. Default to {DEFAULT_VCS_VERSION}"
        )
        return DEFAULT_VCS_VERSION


def get_compose_platform(ssh: bool = False) -> str:
    """Gets the compose platform based on the current environment variables."""
    return "ssh" if ssh else platform.system().lower()


def get_uid() -> int:
    """Gets the current user ID, returning always 1000 in Windows."""
    return os.getuid() if get_compose_platform() != "windows" else 1000


def setup_docker_env(extra_env: dict | None = None):
    """Prepares the current environment variables for docker."""
    # Set the environment variables passed as argument
    os.environ.update(extra_env or {})
    # Set the CI environment variable used by GitHub Actions
    os.environ.setdefault("CI", "false")
    # Use always docker buildkit
    os.environ.setdefault("DOCKER_BUILDKIT", "1")
    os.environ.setdefault("COMPOSE_DOCKER_CLI_BUILD", "1")
    # In Windows, support forward slashes in paths
    os.environ.setdefault("COMPOSE_CONVERT_WINDOWS_PATHS", "1")
    # Set the current user
    os.environ.setdefault("COMPOSE_USER_NAME", getpass.getuser())
    os.environ.setdefault("COMPOSE_USER_UID", str(get_uid()))
    os.environ.setdefault("COMPOSE_USER_GID", "1006")
    os.environ.setdefault("COMPOSE_GROUP_NAME", "ainn")
    # Set the shell
    os.environ.setdefault("COMPOSE_USER_SHELL", os.environ.get("SHELL", "/bin/bash"))

    # Set the docker runtime
    os.environ.setdefault("COMPOSE_RUNTIME", "runc")

    # Set the project version (support empty values from .env file)
    if not os.environ.get("PROJECT_VERSION"):
        os.environ["PROJECT_VERSION"] = get_project_version()

    # Set docker image registry
    os.environ.setdefault("DOCKER_REGISTRY", "elizaprodacreastus2.azurecr.io")
    # Set docker image tag
    os.environ.setdefault("DOCKER_TAG", os.environ["PROJECT_VERSION"])

    # Set the home directory
    home_dir = Path.home().parent.resolve()
    os.environ.setdefault("COMPOSE_HOME_DIR", home_dir.as_posix())
    # Set the cache and data directories
    os.environ.setdefault("COMPOSE_CACHE_DIR", "/tmp")  # noqa: S108
    os.environ.setdefault("COMPOSE_DATA_DIR", "/data")
    # Set the current directory as the code directory
    os.environ.setdefault(
        "COMPOSE_CODE_DIR", Path(__file__).parent.resolve().as_posix()
    )
    # Set artifactory user
    os.environ.setdefault("ARTIFACTORY_PYPI_USER", getpass.getuser())

    # Set the platform (container type)
    os.environ.setdefault("COMPOSE_PLATFORM", "linux")
    # Check that the environment variables are set correctly
    if os.environ["COMPOSE_PLATFORM"] == "ssh" and "COMPOSE_SSH_PORT" not in os.environ:
        raise ValueError("COMPOSE_SSH_PORT environment variable is not set.")


@register_task
def azure_login():
    """Logs in to Azure using az CLI."""
    try:
        run_cmd([*az_cli_cmd(), "ad", "signed-in-user", "show"], capture_output=False)
    except subprocess.CalledProcessError:
        run_cmd([*az_cli_cmd(), "login", "--use-device-code"], capture_output=False)
    print("Azure login successful.")


@register_task
def docker_login():
    """Logs in to the docker registry."""
    azure_login()
    az_token = run_cmd(
        [
            *az_cli_cmd(),
            "acr",
            "login",
            "--name",
            os.environ["DOCKER_REGISTRY"],
            "--expose-token",
            "--output",
            "tsv",
            "--query",
            "accessToken",
        ],
    )
    cmd = [
        "docker",
        "login",
        os.environ["DOCKER_REGISTRY"],
        "--username",
        "00000000-0000-0000-0000-000000000000",
        "--password-stdin",
    ]
    proc = subprocess.Popen(
        cmd,  # noqa: S603
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, stderr = proc.communicate(input=az_token.encode())
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            cmd=cmd,
            returncode=proc.returncode,
            output=output,
            stderr=stderr,
        )
    print("Docker login successful.")


@register_task
def docker_cmd(action: str):
    """Runs a docker command."""
    setup_docker_env()
    docker_login()
    run_cmd(
        cmd=[*docker_compose_cli(), action, os.environ.get("TARGET", "base")],
        capture_output=False,
    )


def manage_dev_container(action: str, ssh: bool = False):
    """Manages the lifecycle of dev and ssh containers."""
    # Always setup the environment before running any command
    setup_docker_env(extra_env={"COMPOSE_PLATFORM": get_compose_platform(ssh)})
    action = os.environ.setdefault("COMPOSE_ACTION", action)
    command = [
        *docker_compose_cli(),
        "-f",
        "docker-compose.yaml",
        "-f",
        "docker-compose.ssh.yaml" if ssh else ".devcontainer/docker-compose.yaml",
        "-p",
        get_compose_project_name(ssh),
        *action.split(),
    ]
    if action != "down":
        command.append("devel")
    run_cmd(command, capture_output=False)


def show_pdm_bootstrap_help():
    """Shows the help message for the pdm bootstrap command."""
    print("🚨 LOCK the deps in your environment by running (one group at a time):")
    print("   pdm add --no-sync -G [default,worker,test,lint,doc,etc]")
    print("🛠  Now, rebuild the container to get a fresh copy of the environment")
    caller = inspect.stack()[1].function
    print(f"   pdm run {caller}")


@register_task
def devcontainer(action: str = "up -d --build"):
    """Manages a devcontainer to attach to using Visual Studio Code."""
    manage_dev_container(action, ssh=False)
    print("🏗️ Run: Ctrl + Shift + P: 'Dev Containers: Attach to Running Container'")
    print("🐚 Open the folder with your project in /workspace and start coding.")
    print("🏗️ Run  Ctrl + Shift + P: 'Show recommended extensions' and install them.")
    show_pdm_bootstrap_help()


@register_task
def sshcontainer(action: str = "up -d --build"):
    """Manages the sshcontainer."""
    manage_dev_container(action, ssh=True)
    ssh_port = os.environ["COMPOSE_SSH_PORT"]
    print(f"🏗️ Connect your your Visual Studio Code to the port {ssh_port}.")
    print("🚨 Make sure your public SSH key is authorized in the host.")
    show_pdm_bootstrap_help()


@register_task
def copy(src: str, dest: str):
    """Copies files from the source to the destination without overwriting."""
    if os.path.exists(dest):
        print(f"Destination {dest} already exists. Skipping.")
    else:
        print(f"Copying {src} to {dest}")
        shutil.copyfile(src, dest)


def run(task: str, *args, **kwargs):
    """Runs the task with the given name."""
    if task not in task_registry:
        raise ValueError(f"Task {task} not found.")
    task_registry[task](*args, **kwargs)


if __name__ == "__main__":
    parser = ArgumentParser(description="Runner for the project.")
    parser.add_argument("task", help="The task to run.")
    parser.add_argument("rest", nargs=REMAINDER)
    args = parser.parse_args()

    # Extract the additional keyword arguments from the CLI
    kwargs = {}
    if args.rest:
        args.rest = [arg.replace("--", "") for arg in args.rest]
        kwargs = dict(zip(args.rest[::2], args.rest[1::2]))
    run(args.task.lower(), **kwargs)

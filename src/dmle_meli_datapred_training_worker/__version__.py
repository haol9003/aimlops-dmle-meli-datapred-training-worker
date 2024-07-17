from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def read_version() -> str:
    """Reads the version from package metadata or from VERSION file."""
    try:
        return version(__package__)
    except PackageNotFoundError:
        try:
            return version("dmle-meli-datapred-training-worker")
        except PackageNotFoundError:
            version_filename = Path(__file__).parent / "VERSION"
            return version_filename.read_text().strip()


__version__ = read_version()

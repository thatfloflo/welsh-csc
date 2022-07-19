import click
from pathlib import Path
from .click_ext import URLParamType
from .get_data import _get_data  # type: ignore


@click.option(
    "-p", "--path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
    default="./data", show_default=True,
    help="The directory where the data files should be stored."
)
@click.option(
    "-r", "--remote",
    type=URLParamType(
        permitted_schemes=("http", "https"), ignore_http_errors=False
    ),
    default="https://data.ling101.com/welsh-csc/data/", show_default=False,
    help="URL for the remote server from which to fetch data. [default: https://data.ling101.com]"
)
def get_meta(path: Path, remote: str):
    """Retrieve metadata for the Welsh CSC data from remote host.

    Existing data files will not be overwritten. To replace files, delete them first (or rename
    them by adding *.bak at the end).

    The data path must already exist and be writeable. By default ./data is assumed
    (relative to the current working directory). A subdirectory named 'meta' will be created
    inside the data path if it does not yet exist.
    """
    # Compute the assets (folders) to be downloaded...
    targets = ["meta"]
    # Report parameters to user
    click.secho("Assets to be downloaded: ", bold=True, nl=False)
    click.echo(", ".join(click.style(target, fg="yellow") for target in targets))
    click.secho("Data directory: ", bold=True, nl=False)
    click.secho(path, fg="yellow")
    for target in targets:
        remote_url = f"{remote}{target}" if remote.endswith("/") else f"{remote}/{target}"
        destination = path / target
        destination.mkdir(exist_ok=True)
        _get_data(remote_url, destination)

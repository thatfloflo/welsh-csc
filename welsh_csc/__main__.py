"""Main CLI interface for the Welsh Controlled Speech Corpus tool."""
import click
from pathlib import Path
from typing import Any


@click.group()
def main(**kwargs: dict[str, Any]):
    """Utility for working with the Welsh Controlled Speech Corpus."""
    pass


@main.command()
@click.option(
    "-d", "--dest",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
    default="./data",
    help="The directory where the data files should be stored.", show_default=True
)
@click.option(
    "-c", "--channel", type=click.Choice(["1", "2", "1+2"]),  default="1+2", show_default=True,
     help="Whether to obtain audio-only (1 ch), audio and lx (2 ch), or both (1+2 ch) versions."
)
@click.argument("component", type=click.Choice(["all", "raw", "chopped"], case_sensitive=False))
def get_data(component: str, dest: Path, channel: str):
    """Retrieve the Welsh CSC data from remote host.
    
    Existing data files will not be overwritten. To replace files, delete them first (or rename
    them by adding *.bak at the end).
    
    The destination path must already exist and be writeable. By default ./data is assumed
    (relative to the current working directory). Depending on the provided options, subdirectories
    with the names raw-1ch, raw-2ch, chopped-1ch, chopped-2ch may be created.
    """
    # Compute the assets (folders) to be downloaded...
    components = ["raw", "chopped"] if component == "all" else [component]
    channels = ["1", "2"] if channel == "1+2" else [channel]
    targets = [f"{component}-{channel}ch" for channel in channels for component in components]
    # Report parameters to user
    click.secho("Assets to be downloaded: ", bold=True, nl=False)
    click.echo(", ".join(click.style(target, fg="yellow") for target in targets))
    click.secho("Destination directory: ", bold=True, nl=False)
    click.secho(dest, fg="yellow")


if __name__ == "__main__":
    main()
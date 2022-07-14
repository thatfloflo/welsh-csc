"""Main CLI interface for the Welsh Controlled Speech Corpus tool."""
import click
import click_spinner
import urllib.request
import urllib.error
import re
import requests
from pathlib import Path
from typing import Any, Container


class URLParamType(click.ParamType):
    name = "URL"

    def __init__(
        self,
        permitted_schemes: Container[str] | None = None,
        default_scheme: str = "http",
        ignore_http_errors: bool = True
    ) -> None:
        super().__init__()
        self.permitted_schemes = permitted_schemes
        self.default_scheme = default_scheme
        self.ignore_http_errors = ignore_http_errors

    def convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> str:
        value = ("://" not in value) * f"{self.default_scheme}://" + value

        scheme, _ = value.split("://", maxsplit=1)
        if self.permitted_schemes and scheme.lower() not in self.permitted_schemes:
            self.fail(f"The URL {scheme!r} is not supported for this parameter")

        try:
            with urllib.request.urlopen(value) as _:
                pass
        except urllib.error.HTTPError as e:
            if not self.ignore_http_errors:
                self.fail(
                    f"The URL {value!r} returned an HTTP Error ([Error {e.code}] {e.reason})",
                    param, ctx
                )
        except urllib.error.URLError as e:
            self.fail(f"{value!r} is not a valid URL or cannot be opened ({e.reason})", param, ctx)

        return value


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
    default="./data", show_default=True,
    help="The directory where the data files should be stored."
)
@click.option(
    "-c", "--channel", type=click.Choice(["1", "2", "1+2"]),  default="1+2", show_default=True,
    help="Whether to obtain audio-only (1 ch), audio and lx (2 ch), or both (1+2 ch) versions."
)
@click.option(
    "-r", "--remote",
    type=URLParamType(
        permitted_schemes=("http", "https"), ignore_http_errors=False
    ),
    default="https://data.ling101.com/welsh-csc/data/", show_default=False,
    help="URL for the remote server from which to fetch data. [default: https://data.ling101.com]"
)
@click.argument("component", type=click.Choice(["all", "raw", "chopped"], case_sensitive=False))
def get_data(component: str, dest: Path, channel: str, remote: str):
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
    for target in targets:
        remote_url = f"{remote}{target}" if remote.endswith("/") else f"{remote}/{target}"
        destination = dest / target
        destination.mkdir(exist_ok=True)
        _get_data(remote_url, destination)


def _get_data(remote_url: str, destination: Path) -> bool:
    click.secho("Fetching files from remote: ", bold=True, nl=False)
    click.secho(remote_url, bold=True, fg="blue")
    index_stack: list[str] = [remote_url]
    item_stack: list[str] = []
    err_stack: list[str] = []
    click.secho("Building index... ", dim=True, nl=False)
    with click_spinner.spinner():  # type: ignore
        while index_stack:
            target_url = index_stack.pop()
            target_url += (not target_url.endswith("/")) * "/"
            r = requests.get(target_url, params={"F": 0})
            if r.status_code == requests.codes.ok:
                items = _parse_apache_index(r.text)
                for item in items:
                    item = f"{target_url}{item}"
                    if item.endswith("/"):
                        index_stack.append(item)
                    else:
                        item_stack.append(item)
            else:
                err_stack.append(target_url)
    click.echo(f"{len(item_stack)} files to fetch")
    for err_url in err_stack:
        click.secho("ERROR: ", bold=True, fg="red", nl=False, err=True)
        click.echo("Could not obtain index for remote directory at ", nl=False, err=True)
        click.secho(err_url, fg="blue", err=True)
    # click.echo(item_stack)
    return True


def _parse_apache_index(html: str) -> list[str]:
    matches = re.findall(
        r"^<li><a href\=\"([\w\-\.\ \%]+/?)\">",
        html,
        flags=re.M
    )
    return matches or []


if __name__ == "__main__":
    main()

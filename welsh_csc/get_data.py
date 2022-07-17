import click
import click_spinner
import requests
import concurrent.futures
import re
from pathlib import Path
from .click_ext import URLParamType, report_http_error, report_url_error, report_exception


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


def _get_data(remote_url: str, destination: Path):
    click.secho("Fetching files from remote: ", bold=True, nl=False)
    click.secho(remote_url, bold=True, fg="blue")
    index = _build_remote_index(remote_url)
    if not index:
        return
    operands = zip(index, map(lambda s: destination / s[len(remote_url)+1:], index))
    session = requests.Session()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(
                _download_file, remote, local, session=session
            ): remote for remote, local in operands
        }
        errors: dict[str, BaseException] = {}
        with click.progressbar(
            length=len(futures),
            label='Downloading files',
            show_eta=True,
            show_pos=True,
            bar_template=click.style('%(label)s  %(bar)s  %(info)s', dim=True),
            empty_char=click.style("▓", fg=240, dim=True),
            fill_char=click.style("█", fg="yellow", dim=False),
            color=True
        ) as pbar:  # type: ignore
            try:
                for future in concurrent.futures.as_completed(futures):
                    pbar.update(1)  # type: ignore
                    if error := future.exception():
                        err_url = futures[future]
                        errors[err_url] = error
            except KeyboardInterrupt:
                click.echo()
                click.secho(
                    "Keyboard Interrupt Caught!",
                    bg="red", fg="white", bold=True, nl=False, err=True
                )
                click.secho(
                    " The process will terminate once all active downloads have finished.",
                    err=True
                )
                executor.shutdown(wait=True, cancel_futures=True)
                raise
        for err_url, error in errors.items():
            if isinstance(error, requests.HTTPError):
                report_http_error(err_url, error.response.status_code)
            elif isinstance(error, IOError):
                report_exception("Could not open file for writing", error)
            else:
                report_url_error(err_url, str(error))


def _download_file(
    remote_url: str,
    destination: Path,
    chunk_size: int = 1_048_576,
    session: requests.Session | None = None
):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb", chunk_size*5, ) as fp:
        getter = session.get if session else requests.get
        r = getter(remote_url, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_size):
            fp.write(chunk)


def _build_remote_index(remote_url: str) -> list[str]:
    index_stack: list[str] = [remote_url]
    item_stack: list[str] = []
    err_stack: list[str] = []
    click.secho("Building index... ", dim=True, nl=False)
    with requests.Session() as session:
        with click_spinner.spinner():  # type: ignore
            while index_stack:
                target_url = index_stack.pop()
                target_url += (not target_url.endswith("/")) * "/"
                r = session.get(target_url, params={"F": 0})
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
    return item_stack


def _parse_apache_index(html: str) -> list[str]:
    matches = re.findall(
        r"^<li><a href\=\"([\w\-\.\ \%]+/?)\">",
        html,
        flags=re.M
    )
    return matches or []

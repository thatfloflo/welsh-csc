import click
import wave
import concurrent.futures
import os
from pathlib import Path
from struct import unpack, pack
from .click_ext import report_exception
from .util import copy_files


@click.option(
    "-p", "--path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
    default="./data", show_default=True,
    help="The directory where the data files are stored."
)
@click.argument("component", type=click.Choice(["all", "raw", "chopped"], case_sensitive=False))
def make_mono(component: str, path: Path):
    """Extract mono voice-tracks from 2 channel audio files.

    Existing data files will not be overwritten. To replace files, delete them first (or rename
    them by adding *.bak at the end).

    The data path must already exist and be writeable. By default ./data is assumed
    (relative to the current working directory). It is assumed that this path contains at least
    one subdirectory named raw-2ch or chopped-2ch. For each of the *-2ch subdirectories, a new
    subdirectory *-1ch will be created if it does not already exist.
    """
    components = ("raw-2ch", "chopped-2ch") if component == "all" else (f"{component}-2ch",)
    # Report parameters to user
    click.secho("Assets to be monoised: ", bold=True, nl=False)
    click.echo(", ".join(click.style(component, fg="yellow") for component in components))
    click.secho("Data directory: ", bold=True, nl=False)
    click.secho(path, fg="yellow")
    for component in components:
        _make_mono(component, path)
        copy_files(
            path / component,
            path / component.replace("-2ch", "-1ch"),
            {".txt", ".TextGrid", ".lab"}
        )


def _make_mono(component: str, path: Path):
    source_path = path / component
    dest_path = path / component.replace("-2ch", "-1ch")
    dest_path.mkdir(exist_ok=True)
    files = [
        (source, Path(str(source).replace(str(source_path), str(dest_path))))
        for source in (
            source for sources in (subpath.glob("*.wav") for subpath in source_path.iterdir())
            for source in sources
        )
    ]
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=min(4, os.cpu_count() or 1)
    ) as executor:
        futures = {
            executor.submit(extract_first_channel, *file): file
            for file in files
        }
        with click.progressbar(
                length=len(futures),
                label='Monoising files',
                show_eta=True,
                show_pos=True,
                bar_template=click.style('%(label)s  %(bar)s  %(info)s', dim=True),
                empty_char=click.style("▓", fg=240, dim=True),
                fill_char=click.style("█", fg="yellow", dim=False),
                color=True
        ) as pbar:  # type: ignore
            error_stack: dict[tuple[Path, Path], BaseException] = {}
            try:
                for future in concurrent.futures.as_completed(futures):
                    pbar.update(1)  # type: ignore
                    if error := future.exception():
                        err_file = futures[future]
                        error_stack[err_file] = error
                click.echo()
            except KeyboardInterrupt:
                click.echo()
                click.secho(
                    "Keyboard Interrupt Caught!",
                    bg="red", fg="white", bold=True, nl=False, err=True
                )
                click.secho(
                    " The process will terminate once all active mono conversions are complete.",
                    err=True
                )
                executor.shutdown(wait=True, cancel_futures=True)
                raise
            for files, error in error_stack.items():
                report_exception(
                    f"Couldn't convert file '{click.style(files[0], fg='yellow')}'",
                    error
                )


def extract_first_channel(source_file: Path, dest_file: Path):
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with wave.open(str(source_file), "rb") as sfp:
            with wave.open(str(dest_file), "wb") as dfp:
                dfp: wave.Wave_write
                dfp.setparams(sfp.getparams())
                dfp.setnchannels(1)
                snframes = sfp.getnframes()
                remaining = snframes
                while remaining > 0:
                    chunk = min(32_768, remaining)
                    remaining -= chunk
                    sframes = sfp.readframes(chunk)
                    sdata = unpack("%dh" % 2*chunk, sframes)
                    ddata = pack("%dh" % chunk, *sdata[0::2])
                    dfp.writeframes(ddata)
    except Exception as e:
        raise Exception(
            f"An error occured while extracting the first channel from the file {source_file}"
        ) from e

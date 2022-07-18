import click
import wave
from pathlib import Path
from struct import unpack, pack
from .click_ext import report_exception


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
    with click.progressbar(
            length=len(files),
            label='Monoising files',
            show_eta=True,
            show_pos=True,
            bar_template=click.style('%(label)s  %(bar)s  %(info)s', dim=True),
            empty_char=click.style("▓", fg=240, dim=True),
            fill_char=click.style("█", fg="yellow", dim=False),
            color=True
    ) as pbar:  # type: ignore
        error_stack: list[Exception] = []
        for file in files:
            try:
                extract_first_channel(*file)
            except Exception as e:
                error_stack.append(e)
            pbar.update(1)  # type: ignore
        for error in error_stack:
            report_exception("Couldn't convert file", error)


def extract_first_channel(source_file: Path, dest_file: Path):
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with wave.open(str(source_file), "rb") as sfp:
            with wave.open(str(dest_file), "wb") as dfp:
                dfp: wave.Wave_write
                dfp.setparams(sfp.getparams())
                dfp.setnchannels(1)
                sframes = sfp.readframes(sfp.getnframes())
                sdata = unpack("%dh" % 2*sfp.getnframes(), sframes)
                ddata = pack("%dh" % sfp.getnframes(), *sdata[0::2])
                dfp.writeframes(ddata)
    except Exception as e:
        raise Exception(
            f"An error occured while extracting the first channel from the file {source_file}"
        ) from e

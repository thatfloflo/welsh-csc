import click
import shutil
import subprocess
import sys
import os
import concurrent.futures
from pathlib import Path
from .util import rglob_by_dir
from .click_ext import report_error, report_exception


@click.option(
    "-p", "--path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
    default="./data", show_default=True,
    help="The directory where the data files are stored."
)
@click.option(
    "-c", "--channel", type=click.Choice(["1", "2", "1+2"]),  default="1+2", show_default=True,
    help="Whether to obtain audio-only (1 ch), audio and lx (2 ch), or both (1+2 ch) versions."
)
def chop_data(path: Path, channel: str):
    """Chop raw audio session files into per-stimulus files.

    Chops any *.wav files found in the raw-1ch and raw-2ch subdirectories of the
    data directory (set by --path, default ./data) using the
    ProRec annotations in the corresponding *.txt file with the same name.

    The chopped files will be placed in the chopped-1ch and chopped-2ch
    subdirectories

    Uses Mark Huckvale's ProChop utility if the utility is found on the path,
    otherwise falls back to prochoppy to chop the audio files.
    """
    channels = ["1", "2"] if channel == "1+2" else [channel]
    targets = [f"raw-{channel}ch" for channel in channels]
    # Report parameters to user
    click.secho("Chopping raw audio for: ", bold=True, nl=False)
    click.echo(", ".join(click.style(target, fg="yellow") for target in targets))
    click.secho("Data directory: ", bold=True, nl=False)
    click.secho(path, fg="yellow")
    for target in targets:
        _chop_data(path, Path(target))


def _chop_data(path: Path, target: Path):
    source_dir = path / target
    if not source_dir.is_dir():
        report_error(
            f"The directory {click.style(source_dir, fg='yellow')} doesn't exist"
        )
        return
    dest_dir = path / Path(str(target).replace("raw", "chopped"))
    files = rglob_by_dir(source_dir, dest_dir, extensions=(".wav"))
    chop = prochop_file if prochop_available() else prochoppy_file
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=min(12, os.cpu_count() or 1)
    ) as executor:
        futures: dict[concurrent.futures.Future[None], tuple[Path, Path]] = {}
        for _, flist in files.items():
            for (source_file, dest_file) in flist:
                futures[
                    executor.submit(chop, source_file, dest_file.parent)
                ] = (source_file, dest_file)
        with click.progressbar(
                length=len(futures),
                label='Chopping files',
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
                    f"Couldn't chop file '{click.style(files[0], fg='yellow')}'",
                    error
                )


def prochop_file(filepath: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "prochop",
            "-a", filepath,
            "-t", filepath.with_suffix(".txt"),
            "-o", dest_dir,
        ],
        stdout=subprocess.DEVNULL
    )


def prochoppy_file(filepath: Path, dest_dir: Path):
    subprocess.run(
        [
            sys.executable,
            "-m", "prochoppy",
            "-a", filepath,
            "-t", filepath.with_suffix(".txt"),
            "-o", dest_dir,
        ],
        stdout=subprocess.DEVNULL
    )


def prochop_available() -> bool:
    return shutil.which("prochop") is not None

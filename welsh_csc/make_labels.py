from typing import Collection
import click
import click_spinner
from pathlib import Path
import shutil
import concurrent.futures
from .click_ext import report_error, progressbar, report_exception
from .util import map_stimulus_to_ascii


@click.option(
    "-p", "--path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
    default="./data", show_default=True,
    help="The directory where the data files are stored."
)
def make_labels(path: Path):
    """Make labels for chopped data files.

    Makes *.lab files from the list of stimuli, which are needed for forced alignment
    with the ProsodyLab Aligner (used by this toolset).

    Assumes that the file meta/stimuli.txt already exists inside the directory defined
    by --path (./data by default). If this is not the case, use the get-meta command
    to obtain it.
    """
    stimulus_file = path / "meta" / "stimuli.txt"
    if not stimulus_file.is_file():
        return report_error(
            f"The stimulus file ({click.style(stimulus_file, fg='yellow')}) "
            f"couldn't be found. Try running the {click.style('get-meta', fg='green', bold=True)} "
            "command first."
        )
    stimuli = stimulus_file.read_text(encoding="utf-8").splitlines()
    click.secho("Making labels for ", bold=True, nl=False)
    click.secho(len(stimuli), fg="yellow", nl=False)
    click.secho(" stimuli ", bold=True)
    click.secho("Data directory: ", bold=True, nl=False)
    click.secho(path, fg="yellow")
    make_label_files(path, stimuli)
    if (path / "chopped-1ch").exists():
        add_labels_to_recordings(path / "chopped-1ch", path / "meta" / "labels")
    if (path / "chopped-2ch").exists():
        add_labels_to_recordings(path / "chopped-2ch", path / "meta" / "labels")


def make_label_files(path: Path, stimuli: Collection[str]):
    with progressbar(stimuli, label="Making label files") as pbar:  # type: ignore
        dest_dir = path / "meta" / "labels"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for stimulus in pbar:
            stimulus: str
            make_label_file(dest_dir, stimulus)


def make_label_file(label_path: Path, stimulus: str):
    ascii_alias = map_stimulus_to_ascii(stimulus)
    stimulus = f"DYWEDA {stimulus.upper()} UNWAITH ETO"
    files = {label_path / f"{ascii_alias}-{n}.lab" for n in (1, 2, 3, 4)}
    for file in files:
        with file.open("w", encoding="utf-8") as fp:
            fp.write(stimulus)


def add_labels_to_recordings(search_path: Path, label_path: Path):
    component = click.style(search_path.name, fg="yellow")
    labels = {label.stem for label in label_path.glob("*.lab")}
    candidate_stack: list[Path] = list(search_path.iterdir())
    file_stack: list[Path] = []
    click.secho(f"Finding audio files for {component}... ", dim=True, nl=False)
    with click_spinner.spinner():  # type: ignore
        while candidate_stack:
            candidate = candidate_stack.pop()
            if candidate.is_dir():
                candidate_stack.extend(candidate.iterdir())
            elif candidate.suffix == ".wav" and candidate.stem in labels:
                file_stack.append(candidate)
    click.echo(f"{len(file_stack)} files to be labelled")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                _copy_file_with_stat,
                label_path / f"{file.stem}.lab",
                file.with_suffix(".lab")
            ): file
            for file in file_stack
        }
        with progressbar(
            length=len(file_stack),
            label=f"Adding labels for {component}"
        ) as pbar:  # type: ignore
            error_stack: dict[Path, BaseException] = {}
            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)  # type: ignore
                if error := future.exception():
                    err_path = futures[future]
                    error_stack[err_path] = error
            for _, error in error_stack.items():
                report_exception("Couldn't copy label file", error)


def _copy_file_with_stat(src: Path, dst: Path):
    shutil.copyfile(src, dst)
    shutil.copystat(src, dst)

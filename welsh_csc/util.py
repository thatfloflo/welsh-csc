import click
import shutil
from pathlib import Path
from typing import Collection


def copy_files(source_dir: Path, dest_dir: Path, extensions: Collection[str] | None = None):
    """Copy all the files matching one of the given extensions from source_dir to dest_dir.

    If extensions is None, all files are copied. To copy annotation files, a good value for
    extension is {".txt", ".TextGrid", ".lab"}
    """
    extensions = extensions or {""}
    if not source_dir.is_dir():
        raise ValueError(f"{source_dir} is not a valid directory")
    dest_dir.mkdir(parents=True, exist_ok=True)
    click.secho("Copying files matching pattern '", bold=True, nl=False)
    click.echo(", ".join(click.style(f"*{ext}", fg="yellow") for ext in extensions) + "'")
    click.secho("Source directory: ", bold=True, nl=False)
    click.secho(source_dir, fg="yellow")
    click.secho("Destination directory: ", bold=True, nl=False)
    click.secho(dest_dir, fg="yellow")
    files = rglob_by_dir(source_dir, dest_dir, extensions)
    nfiles = sum(len(flist) for _, flist in files.items())
    with click.progressbar(
            length=nfiles,
            label='Copying files',
            show_eta=True,
            show_pos=True,
            bar_template=click.style('%(label)s  %(bar)s  %(info)s', dim=True),
            empty_char=click.style("▓", fg=240, dim=True),
            fill_char=click.style("█", fg="yellow", dim=False),
            color=True
    ) as pbar:  # type: ignore
        for rel_dir, flist in files.items():
            (dest_dir / rel_dir).mkdir(parents=True, exist_ok=True)
            for src_file, dest_file in flist:
                shutil.copyfile(src_file, dest_file)
                shutil.copystat(src_file, dest_file)
                pbar.update(1)  # type: ignore


def rglob_by_dir(
    source_dir: Path,
    dest_dir: Path | None = None,
    extensions: Collection[str] | None = None,
    base_dir: Path | None = None
) -> dict[Path, set[tuple[Path, ...]]]:
    """Recusively enumerate files matching extension on path by subdirectory."""
    extensions = extensions or {""}
    extensions = tuple(extensions)
    if base_dir and not source_dir.is_relative_to(base_dir):
        raise ValueError(f"Source dir {source_dir} not relative to base dir {base_dir}")
    paths: dict[Path, set[tuple[Path, ...]]] = {}
    relative_dir = source_dir.relative_to(base_dir) if base_dir else source_dir
    for file in source_dir.iterdir():
        if file.is_dir():
            new_dest_dir = dest_dir / file.name if dest_dir else Path(file.name)
            subpaths = rglob_by_dir(file, new_dest_dir, extensions, base_dir)
            for subpath in subpaths:
                paths[subpath] = subpaths[subpath]
        elif str(file).endswith(extensions):
            if relative_dir not in paths:
                paths[relative_dir] = set()
            paths[relative_dir].add(
                (file, rebase_path(file, source_dir, dest_dir)) if dest_dir else (file,)
            )
    return paths


def rebase_path(path: Path, source_base: Path, target_base: Path) -> Path:
    if not path.is_relative_to(source_base):
        raise ValueError(f"Path {path} not relative to source base {source_base}")
    return target_base / path.relative_to(source_base)


def map_stimulus_to_ascii(string: str):
    mapping: dict[str, str] = {
        'â': 'aa', 'ê': 'ee', 'î': 'ii', 'ô': 'oo', 'û': 'uu', 'ŵ': 'ww', 'ŷ': 'yy',
        'Â': 'AA', 'Ê': 'EE', 'Î': 'II', 'Ô': 'OO', 'Û': 'UU', 'Ŵ': 'WW', 'Ŷ': 'YY',
        'ä': 'a',  'ë': 'e',  'ï': 'i',  'ö': 'o',  'ü': 'u',  'ẅ': 'w',  'ÿ': 'y',
        'Ä': 'A',  'Ë': 'E',  'Ï': 'I',  'Ö': 'O',  'Ü': 'U',  'Ẅ': 'W',  'Ÿ': 'Y',
        'á': 'a',  'é': 'e',  'í': 'i',  'ó': 'o',  'ú': 'u',  'ẃ': 'w',  'ý': 'y',
        'Á': 'A',  'É': 'E',  'Í': 'I',  'Ó': 'O',  'Ú': 'U',  'Ẃ': 'W',  'Ý': 'Y',
        'à': 'a',  'è': 'e',  'ì': 'i',  'ò': 'o',  'ù': 'u',  'ẁ': 'w',  'ỳ': 'y',
        'À': 'A',  'È': 'E',  'Ì': 'I',  'Ò': 'O',  'Ù': 'U',  'Ẁ': 'W',  'Ỳ': 'Y',
    }
    for k, v in mapping.items():
        string = string.replace(k, v)
    return string

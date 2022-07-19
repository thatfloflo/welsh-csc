import click
from pathlib import Path


@click.option(
    "-p", "--path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
    default="./data", show_default=True,
    help="The directory where the data files are stored."
)
def make_labels(path: Path):
    """Make labels for chopped data files."""

    indir = "./stimuli"
    outdir = "./labels"

    labels: dict[str, str] = {}

    p = Path(indir)
    for x in p.iterdir():
        with x.open() as f:
            stimuli = f.readlines()
            for stimulus in stimuli:
                k, v = stimulus.strip("\r\n\t .").split("\t")
                v = v.replace("<em>", "").replace("</em>", "").upper()
                labels[k] = v

    p = Path(outdir)
    for k, v in labels.items():
        fname = p / (k + ".lab")
        with fname.open(mode="w") as f:
            f.write(v)

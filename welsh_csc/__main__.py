"""Main CLI interface for the Welsh Controlled Speech Corpus tool."""
import click
from typing import Any
from .chop_data import chop_data
from .get_data import get_data
from .get_meta import get_meta
from .make_mono import make_mono


@click.group()
def main(**kwargs: dict[str, Any]):
    """Utility for working with the Welsh Controlled Speech Corpus."""
    pass


main.command(chop_data)
main.command(get_data)
main.command(get_meta)
main.command(make_mono)

if __name__ == "__main__":
    main()

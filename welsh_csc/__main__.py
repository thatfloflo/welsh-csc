"""Main CLI interface for the Welsh Controlled Speech Corpus tool."""
import click
from typing import Any
from .get_data import get_data


@click.group()
def main(**kwargs: dict[str, Any]):
    """Utility for working with the Welsh Controlled Speech Corpus."""
    pass


main.command(get_data)

if __name__ == "__main__":
    main()

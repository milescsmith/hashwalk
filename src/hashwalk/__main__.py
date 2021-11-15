"""Command-line interface."""
from hashlib import md5
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

app = typer.Typer(name="hashwalk", help="Generate md5 has for all files along a path.")

console = Console()


def version_callback(value: bool) -> None:
    """Prints the version of the package."""
    if value:
        console.print(
            f"[yellow]{__package__}[/] version: [bold blue]{version(__package__)}[/]"
        )
        raise typer.Exit()


@app.command()
def main(
    path: Path = typer.Argument(
        ".",
        exists=True,
        file_okay=True,
        dir_okay=True,
        resolve_path=True,
        help="Generate hashes for a single file or files in this location",
    ),
    pattern: str = typer.Option(
        "*",
        "-p",
        "--pattern",
        help="Only generate hashes for filenames matching this pattern",
    ),
    recursive: bool = typer.Option(
        False, "-r", "--recursive", help="Search for files recursively"
    ),
    write_individual_files: bool = typer.Option(
        False, "-i", "--individual", help="Write an MD5 file for each hash calculated"
    ),
    output_table: Path = typer.Option(
        None, "-o", "--output", help="Write hashes to table with this filename"
    ),
    full_path_name: bool = typer.Option(
        False,
        "-f",
        "--full-path",
        help="Display the fully resolved file name with path or just the file name",
    ),
    version: bool = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the plinkliftover package.",
    ),
) -> None:
    """Hashwalk."""


    pattern = str(pattern)

    if path.is_dir():
        if recursive:
            pattern = "**/" + pattern
        filelist = path.glob(pattern)

        if full_path_name:
            hashes = {
                str(_.resolve()): md5(_.open("rb").read()).hexdigest()
                for _ in filelist
                if _.is_file()
            }
        else:
            hashes = {
                str(_.name): md5(_.open("rb").read()).hexdigest()
                for _ in filelist
                if _.is_file()
            }
    else:
        if full_path_name:
            hashes = {str(path.resolve()): md5(path.open("rb").read()).hexdigest()}
        else:
            hashes = {str(path.name): md5(path.open("rb").read()).hexdigest()}

    if write_individual_files:
        for i in hashes:
            Path(i).with_suffix(Path(i).suffix + ".md5").write_text(hashes[i])

    if output_table is not None:
        pd.DataFrame.from_dict(data=hashes, orient="index").to_csv(
            path_or_buf=output_table
        )

    if (output_table is None) and (write_individual_files is False):
        for k in hashes:
            console.print(f"[yellow]{k}[/]: [bold blue]{hashes[k]}")


if __name__ == "__main__":
    typer.run(main)  # pragma: no cover

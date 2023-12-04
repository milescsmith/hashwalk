"""Command-line interface."""
import hashlib
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer
from icontract import require
from rich.console import Console

app = typer.Typer(name="hashwalk", help="Generate a hash has for all files along a path.", no_args_is_help=True)

console = Console()


def version_callback(value: bool) -> None:
    """Prints the version of the package."""
    if value:
        console.print(f"[yellow]{__package__}[/] version: [bold blue]{version(__package__)}[/]")
        raise typer.Exit()


# ALGOS = list(hashlib.algorithms_available)
@app.command(no_args_is_help=True)
@require(lambda algorithm: algorithm in hashlib.algorithms_available)
def main(
    path: Annotated[
        Optional[Path],
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            resolve_path=True,
            help="Generate hashes for a single file or files in this location",
        ),
    ] = None,
    pattern: Annotated[
        str,
        typer.Option(
            "-p",
            "--pattern",
            help="Only generate hashes for filenames matching this pattern",
        ),
    ] = "*",
    algorithm: Annotated[
        str,
        typer.Option(
            "-a",
            "--algorithm",
            help="Algorithm to use when generating the hash",
        ),
    ] = "md5",
    recursive: Annotated[bool, typer.Option("-r", "--recursive", help="Search for files recursively")] = False,
    write_individual_files: Annotated[
        bool, typer.Option("-i", "--individual", help="Write an MD5 file for each hash calculated")
    ] = False,
    output_table: Annotated[
        Optional[Path], typer.Option("-o", "--output", help="Write hashes to table with this filename")
    ] = None,
    full_path_name: Annotated[
        bool,
        typer.Option(
            "-f",
            "--full-path",
            help="Display the fully resolved file name with path or just the file name",
        ),
    ] = False,
    version: Annotated[  # noqa: ARG001
        Optional[bool],
        typer.Option(
            None,
            "-v",
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Prints the version of the plinkliftover package.",
        ),
    ] = None,
) -> None:
    """Hashwalk."""

    path = Path().cwd() if path is None else path
    pattern = str(pattern)

    if path.is_dir():
        if recursive:
            pattern = f"**/{pattern}"
        filelist = path.glob(pattern)

        hashes = {
            str(_.resolve()) if full_path_name else str(_.name): make_hash(_, algorithm)
            for _ in filelist
            if _.is_file()
        }
    else:
        hashes = {str(path.resolve()) if full_path_name else str(path.name): make_hash(path, algorithm)}

    if write_individual_files:
        for i in hashes:
            Path(i).with_suffix(f"{Path(i).suffix}.{algorithm}").write_text(hashes[i])

    if output_table is not None:
        pd.DataFrame.from_dict(data=hashes, orient="index").to_csv(path_or_buf=output_table)

    if (output_table is None) and (write_individual_files is False):
        for k in hashes:
            console.print(f"[yellow]{k}[/]: [bold blue]{hashes[k]}")


def make_hash(thing: Path, algorithm: str) -> str:
    text_to_hash = thing.open("rb").read()
    hashobj = hashlib.new(algorithm)
    hashobj.update(text_to_hash)
    return hashobj.hexdigest()

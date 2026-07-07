"""Command-line interface."""

import hashlib
from enum import StrEnum
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer
from joblib import Parallel, delayed
from rich.console import Console
from rich.progress import track

app = typer.Typer(name="hashwalk", help="Generate a hash has for all files along a path.", no_args_is_help=True)

console = Console()


class HashAlgorithm(StrEnum):
    """Hash algorithms available in hashlib."""

    MD5 = "md5"
    SHA1 = "sha1"
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"
    SHAKE_256 = "shake_256"
    BLAKE2S = "blake2s"
    SHA3_384 = "sha3_384"
    SHA_224 = "sha3_224"
    SHA3_256 = "sha3_256"
    SHA3_512 = "sha3_512"
    SHAKE_128 = "shake_128"


def version_callback(value: bool) -> None:
    """Prints the version of the package."""
    if value:
        if __package__ is None:
            console.print("[yellow]hashwalk[/] version: [bold blue]unknown[/]")
        else:
            console.print(f"[yellow]{__package__}[/] version: [bold blue]{version(__package__)}[/]")
        raise typer.Exit()


# ALGOS = list(hashlib.algorithms_available)
@app.command(no_args_is_help=True)
def main(
    path: Annotated[
        Path | None,
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
        HashAlgorithm,
        typer.Option(
            "-a",
            "--algorithm",
            help="Algorithm to use when generating the hash",
        ),
    ] = HashAlgorithm.MD5,
    recursive: Annotated[bool, typer.Option("-r", "--recursive", help="Search for files recursively")] = False,
    write_individual_files: Annotated[
        bool, typer.Option("-i", "--individual", help="Write an MD5 file for each hash calculated")
    ] = False,
    output_table: Annotated[
        Path | None, typer.Option("-o", "--output", help="Write hashes to table with this filename")
    ] = None,
    full_path_name: Annotated[
        bool,
        typer.Option(
            "-f",
            "--full-path",
            help="Display the fully resolved file name with path or just the file name",
        ),
    ] = False,
    n_cpu: Annotated[
        int,
        typer.Option(
            "-n",
            "--n-cpu",
            help="Number of CPUs to use when calculating hashes. Default is all available CPUs.",
        ),
    ] = -1,
    version: Annotated[
        bool | None,
        typer.Option(
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

    parallel = Parallel(n_jobs=n_cpu, backend="loky", prefer="threads", verbose=0, timeout=None, pre_dispatch="2*n_jobs", batch_size="auto")

    if path.is_dir():
        filelist = path.rglob(pattern) if recursive else path.glob(pattern)
        actual_files_list = {f for f in filelist if f.is_file()}
        hashes = parallel(delayed(make_hash)(_, algorithm) for _ in track(actual_files_list, description="Calculating hashes...") if _.is_file())
        hashes = {str(path.resolve()) if full_path_name else str(path.name): _hash for path, _hash in zip(actual_files_list, hashes, strict=True)}
    else:
        hashes = {str(path.resolve()) if full_path_name else str(path.name): make_hash(path, algorithm)}

    if write_individual_files:
        for i in hashes:
            Path(i).with_suffix(f"{Path(i).suffix}.{algorithm}").write_text(hashes[i])

    if output_table is not None:
        with open(output_table, "w", encoding="utf-8") as f:
            f.write(f"path,filename,{algorithm}\n")
            for key, value in hashes.items():
                f.write(f"{Path(key).parent},{Path(key).name},{value}\n")

    if (output_table is None) and (write_individual_files is False):
        for k in hashes:
            console.print(f"[yellow]{k}[/]: [bold blue]{hashes[k]}")


def make_hash(thing: Path, algorithm: str) -> str:
    text_to_hash = thing.open("rb").read()
    hashobj = hashlib.new(algorithm)
    hashobj.update(text_to_hash)
    return hashobj.hexdigest()

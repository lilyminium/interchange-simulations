import json
import time
import pathlib
import click
import tqdm
import os

from openff.units import unit
from openff.units.openmm import from_openmm
from openmm import NonbondedForce
from openff.toolkit import Molecule, Topology, ForceField
from openff.evaluator.utils.packmol import pack_box
from openff.interchange import Interchange

TARGET_DENSITY = 0.95 * unit.grams / unit.mL

@click.command()
@click.option(
    "--input-file",
    "-i",
    default="liquid-boxes.json",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Input file",
)
@click.option(
    "--force-field",
    "-ff",
    default="openff-2.2.1.offxml",
    type=str,
    help="Force field",
)
@click.option(
    "--output-directory",
    "-o",
    default="n-1000",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory",
)
@click.option(
    "--index",
    "-idx",
    default=0,
    type=int,
    help="Index",
)
def main(
    input_file: str,
    force_field: str,
    output_directory: str,
    index: int,
):
    with open(input_file, "r") as f:
        data = json.load(f)

    force_field = ForceField(force_field)
    output_directory = pathlib.Path(output_directory)

    i = index
    box = data[i]
    mols = [
        Molecule.from_smiles(smiles, allow_undefined_stereo=True) for smiles in box["smiles"]
    ]
    n_molecules = box["n_molecules"]

    solute = None
    if n_molecules[0] == 1:
        solute = mols.pop(0).to_topology()
        n_molecules.pop(0)

    entry_directory = output_directory / f"entry-{i:04d}"
    entry_directory.mkdir(parents=True, exist_ok=True)

    os.chdir(str(entry_directory))
    
    start_time = time.time()
    try:
        trajectory, resnames = pack_box(
            molecules=mols,
            number_of_copies=n_molecules,
            structure_to_solvate=None,
            center_solute=True,
            mass_density=TARGET_DENSITY,
            box_aspect_ratio=[1, 1, 1],
            verbose=True,
            working_directory=".",
            retain_working_files=True,
        )
    except Exception as e:
        print(f"Failed to pack box {i:04d}")
        error_file =  "error.txt"
        with open(error_file, "w") as f:
            f.write(str(e))
        raise e

    end_time = time.time()
    difference = end_time - start_time
    print(f"Entry {i}: {difference}")

    topology_molecules = []
    for mol, n in zip(mols, n_molecules):
        topology_molecules.extend([mol] * n)
    solvated_topology = Topology.from_molecules(topology_molecules)

    interchange = Interchange.from_smirnoff(force_field, solvated_topology)
    interchange.positions = (
        trajectory.xyz[0] * unit.nanometers
    )
    print(n_molecules)
    print(trajectory.xyz.shape)

    serialized_file = "interchange.json"
    with open(serialized_file, "w") as f:
        f.write(interchange.json())
    
    trajectory.save_pdb("input.pdb")
    interchange.to_gro("input.gro")
    interchange.to_top("system.top")

    timing = {"time": difference}
    with open("time.json", "w") as f:
        json.dump(timing, f)


if __name__ == "__main__":
    main()

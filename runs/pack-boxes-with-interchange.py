import json
import pathlib
import click
import tqdm

from openff.units import unit
from openff.units.openmm import from_openmm
from openmm import NonbondedForce
from openff.toolkit import Molecule, Topology, ForceField
from openff.interchange.components._packmol import pack_box, UNIT_CUBE
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
def main(
    input_file: str,
    force_field: str,
    output_directory: str,
):
    with open(input_file, "r") as f:
        data = json.load(f)

    force_field = ForceField(force_field)
    output_directory = pathlib.Path(output_directory)

    for i, box in enumerate(tqdm.tqdm(data, desc="packing boxes")):
        mols = [
            Molecule.from_smiles(smiles, allow_undefined_stereo=True) for smiles in box["smiles"]
        ]
        for mol in mols:
            mol.generate_conformers()
        n_molecules = box["n_molecules"]

        solute = None
        if n_molecules[0] == 1:
            solute = mols.pop(0).to_topology()
            n_molecules.pop(0)
        
        try:
            solvated_topology = pack_box(
                molecules=mols,
                number_of_copies=n_molecules,
                solute=solute,
                target_density=TARGET_DENSITY,
                box_shape=UNIT_CUBE,
                center_solute=True,
                working_directory=None,
                retain_working_files=False,
            )
        except Exception as e:
            print(f"Failed to pack box {i:04d}")
            print(e)
            continue

        interchange = Interchange.from_smirnoff(force_field, solvated_topology)

        entry_directory = output_directory / f"entry-{i:04d}"
        entry_directory.mkdir(parents=True, exist_ok=True)

        serialized_file = entry_directory / "interchange.json"
        with open(serialized_file, "w") as f:
            f.write(interchange.json())
        
        interchange.to_pdb(entry_directory / "input.pdb")
        interchange.to_gro(entry_directory / "input.gro")
        interchange.to_top(entry_directory / "system.top")


if __name__ == "__main__":
    main()

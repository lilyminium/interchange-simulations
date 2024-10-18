from openff.units import unit
from openff.units.openmm import from_openmm
from openmm import NonbondedForce
from openff.toolkit import Molecule, Topology, ForceField
from openff.interchange.components._packmol import pack_box, UNIT_CUBE
from openff.interchange import Interchange
import pytest

if __name__ == "__main__":

    solvent = Molecule.from_smiles('CCCCO')
    solvent.generate_conformers()
    solvent.assign_partial_charges(partial_charge_method='am1bcc')

    ligand = Molecule.from_smiles('CCCCCCCC')
    ligand.generate_conformers()
    ligand.assign_partial_charges(partial_charge_method='am1bcc')

    off_top = Topology.from_molecules(ligand)
    solvated_off_top = pack_box(
        molecules=[solvent],
        number_of_copies=[2000],
        solute=off_top,
        tolerance=2.0*unit.angstrom,
        mass_density=0.95 * unit.gram/unit.milliliter,
        box_shape=UNIT_CUBE,
        center_solute=True,
        working_directory='failure',
        retain_working_files=True,
    )

    print("succeeded -- failure")

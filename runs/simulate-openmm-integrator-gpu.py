import click
import tqdm
import json
import pathlib

import openmm
import openmmtools
import openff.toolkit
import openff.units
import openff.interchange
import openff.evaluator
from openff.toolkit import Molecule, ForceField, Topology

import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
import MDAnalysis as mda

from openff.units import unit
from openff.units.openmm import from_openmm, to_openmm
from openff.interchange import Interchange
from openff.evaluator.protocols.openmm import OpenMMSimulation


def create_openmm_objects(
    interchange: Interchange,
    temperature: unit.Quantity = 298.15 * unit.kelvin,
    pressure: unit.Quantity = 1.0 * unit.atmospheres,
    collision_rate: unit.Quantity = 1.0 / unit.picoseconds,
    timestep: unit.Quantity = 2.0 * unit.femtoseconds,  # 2 fs
    n_barostat_steps: int = 25,
):
    
    system = interchange.to_openmm_system()

    openmm_state = openmmtools.states.ThermodynamicState(
        system=system,
        temperature=to_openmm(temperature),
        pressure=to_openmm(pressure)
    )
    
    system = openmm_state.get_system(remove_thermostat=True)

    integrator = openmmtools.integrators.LangevinIntegrator(
        temperature=to_openmm(temperature),
        collision_rate=to_openmm(collision_rate),
        timestep=to_openmm(timestep),
    )

    platform = openmm.Platform.getPlatformByName("CUDA")
    context = openmm.Context(system, integrator, platform)

    # update context
    context.setPeriodicBoxVectors(*to_openmm(interchange.box))
    context.setPositions(to_openmm(interchange.positions))
    return context, integrator


def simulate(
    interchange: Interchange,
    name: str,
    temperature: unit.Quantity = 298.15 * unit.kelvin,
    pressure: unit.Quantity = 1.0 * unit.atmospheres,
    collision_rate: unit.Quantity = 1.0 / unit.picoseconds,
    timestep: unit.Quantity = 2.0 * unit.femtoseconds,  # 2 fs
    n_barostat_steps: int = 25,
    n_total_steps: int = 1000000,
    output_frequency: int = 1000,
):
    context, integrator = create_openmm_objects(
        interchange,
        temperature=temperature,
        pressure=pressure,
        collision_rate=collision_rate,
        timestep=timestep,
        n_barostat_steps=n_barostat_steps,
    )
    dcd_reporter = OpenMMSimulation._DCDReporter(
        f"{name}.dcd",
        False,
    )
    csv_reporter = openmm.app.StateDataReporter(
        f"{name}.csv",
        output_frequency,
        step=True,
        time=True,
        potentialEnergy=True,
        kineticEnergy=True,
        totalEnergy=True,
        temperature=True,
        volume=True,
        density=True,
        speed=True,
        separator=",",
    )

    current_step = 0
    simulation = OpenMMSimulation._Simulation(
        integrator,
        interchange.to_openmm_topology(),
        interchange.to_openmm_system(),
        context,
        current_step,
    )


    while current_step < n_total_steps:
        integrator.step(output_frequency)
        current_step += output_frequency
        state = context.getState(
            getPositions=True,
            getEnergy=True,
            getVelocities=False,
            getForces=False,
            getParameters=False,
            enforcePeriodicBox=True,
        )
        simulation.currentStep = current_step
        dcd_reporter.report(simulation, state)
        csv_reporter.report(simulation, state)

    # plot statistics
    df = pd.read_csv(f"{name}.csv")
    cols = [x for x in df.columns if (x != '#"Step"' and "Speed" not in x)]
    melted = df.melt(
        id_vars=["Time (ps)"],
        value_vars=cols,
        var_name="Quantity",
        value_name="Value"
    )
    g = sns.FacetGrid(melted, col="Quantity", col_wrap=3, sharey=False, sharex=False)
    g.map(sns.lineplot, "Time (ps)", "Value")
    g.set_titles("{col_name}")
    g.savefig(f"{name}_statistics.png", dpi=300)

    return simulation


@click.command()
@click.option(
    "--input-directory",
    "-i",
    default=".",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Input directory",
)
@click.option(
    "--input-file",
    "-if",
    default="../../liquid-boxes.json",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Input file",
)
@click.option(
    "--input-pdb",
    "-ip",
    default="input.pdb",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Input PDB file",
)
@click.option(
    "--index",
    "-idx",
    default=0,
    type=int,
    help="Index",
)
@click.option(
    "--force-field",
    "-ff",
    default="openff-2.2.1.offxml",
    type=str,
    help="Force field",
)
@click.option(
    "--n-equilibration-steps",
    "-ne",
    default=100000,
    type=int,
    help="Number of equilibration steps",
)
@click.option(
    "--n-production-steps",
    "-np",
    default=1000000,
    type=int,
    help="Number of production steps",
)
@click.option(
    "--timestep",
    "-dt",
    default=2.0,
    type=float,
    help="Timestep in fs",
)
@click.option(
    "--n-barostat-steps",
    "-nb",
    default=25,
    type=int,
    help="Number of barostat steps",
)
def main(
    input_file: str,
    input_pdb: str,
    index: int,
    force_field: str,
    input_directory: str,
    n_equilibration_steps: int = 100000,
    n_production_steps: int = 1000000,
    timestep: float = 2.0,
    n_barostat_steps: int = 25,
):

    input_directory = pathlib.Path(input_directory)
    output_subdirectory = f"ne-{n_equilibration_steps}_np-{n_production_steps}_dt-{timestep}_nb-{n_barostat_steps}-omm-int-gpu"
    output_directory = input_directory / output_subdirectory
    output_directory.mkdir(exist_ok=True, parents=True)

    # save provenance
    package_versions = {}
    package_versions["openmm"] = openmm.__version__
    package_versions["openmmtools"] = openmmtools.__version__
    package_versions["openff.toolkit"] = openff.toolkit.__version__
    package_versions["openff.units"] = openff.units.__version__
    package_versions["openff.interchange"] = openff.interchange.__version__
    package_versions["openff.evaluator"] = openff.evaluator.__version__

    with (output_directory / "package-versions.json").open("w") as f:
        json.dump(package_versions, f, indent=2)

    # interchange = Interchange.parse_file(input_directory / "interchange.json")

    # interchange 0.3.x is not compatible with 0.4.x, so we have to re-create it
    # reread from inputs...
    with open(input_file, "r") as f:
        data = json.load(f)

    force_field = ForceField(force_field)
    i = index
    box = data[i]
    mols = []
    for smiles, n_molecules in zip(box["smiles"], box["n_molecules"]):
        mol = Molecule.from_smiles(smiles, allow_undefined_stereo=True)
        mols.extend([mol] * n_molecules)
    
    topology = Topology.from_molecules(mols)
    interchange = Interchange.from_smirnoff(force_field, topology)
    u = mda.Universe(input_pdb)
    interchange.positions = u.atoms.positions * unit.angstrom
    box = np.eye(3) * u.dimensions[:3] * unit.angstrom
    interchange.box = box
    

    
    print("Minimizing...")

    # minimize. Roughly approximates Evaluator
    interchange.minimize(max_iterations=0)

    # save the minimized structure
    with (output_directory / "minimized-interchange.json").open("w") as f:
        f.write(interchange.json())
    interchange.to_pdb(output_directory / "minimized.pdb")
    interchange.to_gro(output_directory / "minimized.gro")

    print("Equilibrating...")

    # equilibrate
    equilibration = simulate(
        interchange,
        name=output_directory / "equilibration",
        n_total_steps=n_equilibration_steps,
        timestep=timestep * unit.femtoseconds,
        n_barostat_steps=n_barostat_steps,
    )
    state = equilibration.context.getState(getPositions=True)
    box_vectors = state.getPeriodicBoxVectors() 
    equilibrated_positions = state.getPositions(asNumpy=True)
    interchange.positions = from_openmm(equilibrated_positions)
    interchange.box = from_openmm(box_vectors)

    interchange.to_pdb(output_directory / f"equilibrated.pdb")

    print("Simulating...")

    # simulate
    production = simulate(
        interchange,
        name=output_directory / "production",
        n_total_steps=n_production_steps,
        timestep=timestep * unit.femtoseconds,
        n_barostat_steps=n_barostat_steps,
    )
    production_positions = production.context.getState(getPositions=True).getPositions(asNumpy=True)
    interchange.positions = from_openmm(production_positions)
    interchange.to_pdb(input_directory / f"{output_subdirectory}.pdb")


if __name__ == "__main__":
    main()

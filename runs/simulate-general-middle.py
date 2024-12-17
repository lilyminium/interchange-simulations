import click
import logging
import tqdm
import pathlib
import sys

import openmm
import openmmtools
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from openff.units import unit
from openff.units.openmm import from_openmm, to_openmm
from openff.interchange import Interchange


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def create_openmm_simulation(
    interchange: Interchange,
    friction_coefficient: int = 1,
    temperature: unit.Quantity = 298.15 * unit.kelvin,
    pressure: unit.Quantity = 1.0 * unit.atmospheres,
    timestep: unit.Quantity = 2.0 * unit.femtoseconds,  # 2 fs
    n_barostat_steps: int = 25,
    hydrogen_mass: int = 1,
):
    collision_rate = friction_coefficient / unit.picoseconds
    integrator = openmm.openmm.LangevinMiddleIntegrator(
        to_openmm(temperature),
        to_openmm(collision_rate),
        to_openmm(timestep),
    )
    barostat = openmm.MonteCarloBarostat(
        to_openmm(pressure),
        to_openmm(temperature),
        n_barostat_steps,
    )
    simulation = interchange.to_openmm_simulation(
        integrator=integrator,
        additional_forces=[barostat],
        hydrogen_mass=1.007947 * hydrogen_mass
    )
    return simulation


def simulate(
    interchange: Interchange,
    name: str,
    friction_coefficient: int = 1,
    temperature: unit.Quantity = 298.15 * unit.kelvin,
    pressure: unit.Quantity = 1.0 * unit.atmospheres,
    timestep: unit.Quantity = 2.0 * unit.femtoseconds,  # 2 fs
    n_barostat_steps: int = 25,
    n_total_steps: int = 1000000,
    output_frequency: int = 1000,
    hydrogen_mass: int = 1,
):
    simulation = create_openmm_simulation(
        interchange,
        friction_coefficient=friction_coefficient,
        temperature=temperature,
        pressure=pressure,
        timestep=timestep,
        n_barostat_steps=n_barostat_steps,
        hydrogen_mass=hydrogen_mass
    )
    simulation.reporters.append(
        openmm.app.DCDReporter(
            f"{name}.dcd",
            output_frequency,
        )
    )
    simulation.reporters.append(
        openmm.app.StateDataReporter(
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
    )
    steps = list(range(n_total_steps // 10))
    for i in tqdm.tqdm(steps):
        simulation.step(10)

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
@click.option(
    "--friction-coefficient",
    "-fc",
    default=1,
    type=float,
    help="Friction coefficient"
)
@click.option(
    "--suffix",
    "-sf",
    default="",
    type=str,
    help="suffix",
)
@click.option(
    "--hydrogen-mass",
    "-hm",
    default=1,
    type=float,
    help="Hydrogen mass for HMR, in amu"
)
def main(
    input_directory: str,
    friction_coefficient: int = 1,
    n_equilibration_steps: int = 100000,
    n_production_steps: int = 1000000,
    timestep: float = 2.0,
    n_barostat_steps: int = 25,
    suffix: str = "",
    hydrogen_mass: int = 1,
):

    input_directory = pathlib.Path(input_directory)
    # check type of hydrogen_mass...
    if hydrogen_mass == int(hydrogen_mass):
        hydrogen_mass = int(hydrogen_mass)
    output_subdirectory = f"ne-{n_equilibration_steps}_np-{n_production_steps}_dt-{timestep}_nb-{n_barostat_steps}_fc-{friction_coefficient}_h{hydrogen_mass}{suffix}"
    output_directory = input_directory / output_subdirectory
    output_directory.mkdir(exist_ok=True, parents=True)
    # quit early if file exists
    output_file = input_directory / f"{output_subdirectory}.pdb"
    if output_file.exists():
        print(f"{output_file} exists")
        return

    interchange = Interchange.parse_file(input_directory / "interchange.json")
    
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
        friction_coefficient=friction_coefficient,
        name=output_directory / "equilibration",
        n_total_steps=n_equilibration_steps,
        timestep=timestep * unit.femtoseconds,
        n_barostat_steps=n_barostat_steps,
        hydrogen_mass=hydrogen_mass
    )
    state = equilibration.context.getState(getPositions=True)
    box_vectors = state.getPeriodicBoxVectors() 
    equilibrated_positions = state.getPositions(asNumpy=True)
    interchange.positions = from_openmm(equilibrated_positions)
    interchange.box = from_openmm(box_vectors)

    interchange.to_pdb(output_directory / "equilibrated.pdb")

    print("Simulating...")

    # simulate
    production = simulate(
        interchange,
        friction_coefficient=friction_coefficient,
        name=output_directory / "production",
        n_total_steps=n_production_steps,
        timestep=timestep * unit.femtoseconds,
        n_barostat_steps=n_barostat_steps,
        hydrogen_mass=hydrogen_mass,
    )
    production_positions = production.context.getState(getPositions=True).getPositions(asNumpy=True)
    interchange.positions = from_openmm(production_positions)
    interchange.to_pdb(output_file)
    interchange.to_pdb(output_directory / "final.pdb")


if __name__ == "__main__":
    main()

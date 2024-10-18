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
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def create_openmm_simulation(
    interchange: Interchange,
    temperature: unit.Quantity = 298.15 * unit.kelvin,
    pressure: unit.Quantity = 1.0 * unit.atmospheres,
    collision_rate: unit.Quantity = 1.0 / unit.picoseconds,
    timestep: unit.Quantity = 2.0 * unit.femtoseconds,  # 2 fs
    n_barostat_steps: int = 25,
):
    integrator = openmmtools.integrators.LangevinIntegrator(
        temperature=to_openmm(temperature),
        collision_rate=to_openmm(collision_rate),
        timestep=to_openmm(timestep),
    )
    barostat = openmm.MonteCarloBarostat(
        to_openmm(pressure),
        to_openmm(temperature),
        n_barostat_steps,
    )
    simulation = interchange.to_openmm_simulation(
        integrator=integrator,
        additional_forces=[barostat],
    )
    return simulation


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
    simulation = create_openmm_simulation(
        interchange,
        temperature=temperature,
        pressure=pressure,
        collision_rate=collision_rate,
        timestep=timestep,
        n_barostat_steps=n_barostat_steps,
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
def main(
    input_directory: str,
    n_equilibration_steps: int = 100000,
    n_production_steps: int = 1000000,
    timestep: float = 2.0,
    n_barostat_steps: int = 25,
):

    input_directory = pathlib.Path(input_directory)
    output_subdirectory = f"ne-{n_equilibration_steps}_np-{n_production_steps}_dt-{timestep}_nb-{n_barostat_steps}"
    output_directory = input_directory / output_subdirectory
    output_directory.mkdir(exist_ok=True, parents=True)

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

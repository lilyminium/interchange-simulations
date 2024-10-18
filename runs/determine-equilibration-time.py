import pathlib
import tqdm

import click
import numpy as np
import pandas as pd
from pymbar.timeseries import detect_equilibration


@click.command()
@click.option(
    "--input-directory",
    "-i",
    default="boxes-nosort/n-1000",
    type=str,
    help="Input directory",
)
@click.option(
    "--run",
    "-r",
    default="ne-2500000_np-1000000_dt-2.0_nb-25",
    type=str,
    help="Run",
)
@click.option(
    "--output-file",
    "-o",
    default="boxes-nosort_n-1000_equilibration.csv",
    type=str,
    help="Output file",
)
def main(
    input_directory: str = "boxes-nosort/n-1000",
    run: str = "ne-2500000_np-1000000_dt-2.0_nb-25",
    output_file: str = "boxes-nosort_n-1000_equilibration.csv"
):
    input_directory = pathlib.Path(input_directory)
    pattern = f"*/{run}/production.csv"
    production_files = sorted(input_directory.glob(pattern))

    entries = []

    for production_csv in tqdm.tqdm(production_files):
        equilibration_csv = production_csv.parent / "equilibration.csv"

        df = pd.concat([
            pd.read_csv(equilibration_csv),
            # pd.read_csv(production_csv)
        ])

        # just assume step size is 1000, dt is 2 ps
        df['#"Step"'] = np.arange(1, len(df) + 1, dtype=float) * 1000
        df["Time (ps)"] = df['#"Step"'] * 2 / 1000
        #combined_csv = production_csv.parent / "combined.csv"
        #df.to_csv(combined_csv)
        #print(f"Combined csv saved to {combined_csv}")

        # detect equilibration
        ignore_cols = ['#"Step"', 'Time (ps)']
        for col in df.columns:
            if col in ignore_cols:
                continue
            t0, g, Neff_max = detect_equilibration(df[col])
            entry = {
                "entry": int(production_csv.parent.parent.name.split("-")[1]),
                "run": run,
                "property": col,
                "t0": t0,
                "g": g,
                "Neff_max": Neff_max
            }
            entries.append(entry)
        
    df = pd.DataFrame(entries)
    df.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()

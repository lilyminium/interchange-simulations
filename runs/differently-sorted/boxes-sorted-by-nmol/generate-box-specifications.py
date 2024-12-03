"""
The first version of box generation tried.
This sorts by the number of molecules in the box,
such that the smallest proportion is first.
"""

import click
import json
import pandas as pd

def turn_property_into_boxes(
    entry: dict,
    n_molecules: int,
) -> set[tuple[tuple[str, int], ...]]:
    all_boxes = set()
    main_box = []
    assert sum([component["mole_fraction"] for component in entry["components"]]) == 1.0
    for component in entry["components"]:
        main_box.append((component["smiles"], int(round(component["mole_fraction"] * n_molecules))))
        all_boxes.add(((component["smiles"], n_molecules),))
    main_box.sort(key=lambda x: x[::-1])
    all_boxes.add(tuple(main_box))
    return all_boxes


@click.command()
@click.option(
    "--n-molecules",
    "-n",
    default=1000,
    type=int,
    help="Number of molecules in the box",
)
@click.option(
    "--output-file",
    "-o",
    default="liquid-boxes.json",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Output file",
)
def main(
    n_molecules: int = 1000,
    output_file: str = "liquid-boxes.json",
):
    with open("../data/sage-train-v1.json", "r") as f:
        data = json.load(f)

    all_boxes = set()

    for entry in data["entries"]:
        all_boxes |= turn_property_into_boxes(entry, n_molecules)
    
    df = pd.read_csv("../data/full_results_mnsol_2_0_0.csv")
    for solvent in df.Solvent.unique():
        all_boxes.add(((solvent, n_molecules),))
    
    for _, row in df.iterrows():
        solute = row.Solute
        solvent = row.Solvent
        all_boxes.add(((solute, 1), (solvent, n_molecules - 1)))
    
    all_boxes = sorted(all_boxes, key=lambda x: (len(x), x[0][1], x))
    output = []
    for box in all_boxes:
        output.append({
            "smiles": [component[0] for component in box],
            "n_molecules": [component[1] for component in box],
        })

    with open(output_file, "w") as f:
        json.dump(output, f, indent=4)
    print(f"Wrote {len(output)} boxes to {output_file}")


if __name__ == "__main__":
    main()


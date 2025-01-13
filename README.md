# Interchange equilibration times

This repo documents some experimentation with simulation of liquid boxes created through interchange.
It addresses two issues: general packing of boxes, and equilibration times.

## Data

The boxes packed here are combinations of mixtures in the [Sage training and testing data](https://github.com/openforcefield/openff-sage/tree/main/data-set-curation), specifically the training set and subset from MNSol.

Box specifications were generated [by multiplying the mole fraction of each substance by the required number of molecules.](runs/boxes-nosort/generate-box-specifications-nosort.py) This repo looks at boxes of both 1000 and 2000 molecules, focusing more on the latter.
The script generates box specifications as a list of dictionaries specifying the SMILES of each molecule and the number of each molecule.
An example file is [liquid-boxes.json](runs/boxes-nosort/n-2000/liquid-boxes.json).

## Box packing

When only one conformer is generated per compound, boxes can be generally and broadly packed using
the Interchange Packmol wrapper for all compounds, using default arguments.

From the Interchange release *after* 0.4.10, this should be default behaviour.

## Simulation

There were no issues running equilibration and productions simulations using Interchange-created systems and packed boxes,
without and with HMR (latter not uploaded).

## Equilibration

Equilibration was detected using [Pymbar's detect_equilibration function](runs/determine-equilibration-time.py)

![n-2000 equilibration times of different properties](runs/images/boxes-nosort_n-2000_interchange-equilibration.png?raw=True)


In the majority of simulations, each box equilibrated by 5 ns.
For SFE boxes where there is only one molecule of ligand in a box of solvent, the *vast* majority of boxes equilibrated by 5 ns.

Problematic "SFE" boxes largely included large and floppy molecules, such as `CCCCOP(=O)(OCCCC)OCCCC` as the solvent.
Problematic boxes of general liquid properties suggested that other compounds, such as
[NCCNCCN](runs/boxes-nosort/n-2000/images/ne-6000000_np-5000000_dt-2.0_nb-25_fc-1/equilibration/entry-0113.png) and
[OCCN(CCO)CCO](runs/boxes-nosort/n-2000/images/ne-6000000_np-5000000_dt-2.0_nb-25_fc-1/equilibration/entry-0125.png)
do equilibrate very, very slowly.

The slower systems have been saved [here for 5 ns](runs/long_equilibration_boxes_over_5ns.json)
and [here for 10 ns](runs/long_equilibration_boxes_over_10ns.json).
Plots of properties for the problematic boxes have [also been saved.](runs/boxes-nosort/n-2000/images/ne-6000000_np-5000000_dt-2.0_nb-25_fc-1/equilibration/)

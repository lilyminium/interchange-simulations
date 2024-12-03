#!/usr/bin/env bash
#SBATCH -J detect-equilibration
#SBATCH -p standard
#SBATCH -t 72:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account dmobley_lab
#SBATCH --output slurm-%x.%A.out

. ~/.bashrc

# Use the right conda environment
conda activate interchange-packmol-040-final

BOXES="boxes-nosort"
NMOL=1000
# NEQ=100000
NEQ=2500000
NPROD=1000000
TIMESTEP='2.0'
NBAROSTAT=25

RUN="ne-${NEQ}_np-${NPROD}_dt-${TIMESTEP}_nb-${NBAROSTAT}"
INPUT_DIRECTORY="${BOXES}/n-${NMOL}/runs-interchange-final"
OUTPUT_FILES="${BOXES}_n-${NMOL}_interchange-equilibration.csv"

python determine-equilibration-time.py -i $INPUT_DIRECTORY -o $OUTPUT_FILES -r $RUN

#!/usr/bin/env bash
#SBATCH -J pack-boxes
#SBATCH -p standard
#SBATCH -t 24:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account dmobley_lab
#SBATCH --output slurm-%x.%A.out

# ===================== conda environment =====================
. ~/.bashrc
conda activate interchange-packmol-040


NMOL=1000

python pack-boxes-with-interchange.py  -i "n-${NMOL}/liquid-boxes.json" -o "n-${NMOL}/runs"



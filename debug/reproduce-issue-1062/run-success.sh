#!/usr/bin/env bash
#SBATCH -J issue-1062
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
conda activate interchange-packmol-040-final

mkdir success
python pack-success.py


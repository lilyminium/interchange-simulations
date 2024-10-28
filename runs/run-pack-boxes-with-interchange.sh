#!/usr/bin/env bash
#SBATCH -J pack-boxes
#SBATCH --array=0-1411%100
#SBATCH -p free
#SBATCH -t 24:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account dmobley_lab
#SBATCH --output run-logs/slurm-%x.%A-%a.out

# ===================== conda environment =====================
. ~/.bashrc
conda activate interchange-packmol-040

# 1000: 1412 boxes

NMOL=1000

if [ ! -f "input.pdb" ] ; then
    python pack-boxes-with-interchange.py  -i "n-${NMOL}/liquid-boxes.json" -o "n-${NMOL}/runs" -idx $SLURM_ARRAY_TASK_ID
fi



#!/usr/bin/env bash
#SBATCH -J pack-boxes-interchange
#SBATCH --array=1248-1248%300
#SBATCH -p standard
#SBATCH -t 24:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account dmobley_lab
#SBATCH --output run-logs/slurm-%x.%A-%a.out

# ===================== conda environment =====================
. ~/.bashrc
conda activate interchange-packmol-040-final

# 1000: 1412 boxes
# 2000: 1449 boxes

NMOL=1000
BOXES="boxes-nosort"

if [ ! -f "input.pdb" ] ; then
    python pack-boxes-with-interchange.py  -i "${BOXES}/n-${NMOL}/liquid-boxes.json" -o "${BOXES}/n-${NMOL}/runs-interchange-final" -idx $SLURM_ARRAY_TASK_ID
fi



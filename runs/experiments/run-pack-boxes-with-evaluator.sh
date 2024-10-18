#!/usr/bin/env bash
#SBATCH -J pack-boxes
#SBATCH --array=1036-1036%300
#SBATCH -p standard
#SBATCH -t 24:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account [xxx]
#SBATCH --output run-logs/slurm-%x.%A-%a.out

# ===================== conda environment =====================
. ~/.bashrc
conda activate evaluator-0-4-10

# 1000: 1412 boxes

# 6421: 1248 in boxes-sorted-by-nmol
# 6421: 1036 in boxes-nosort

NMOL=1000
BOXES="boxes-nosort"

if [ ! -f "input.pdb" ] ; then
    python pack-boxes-with-evaluator.py  -i "${BOXES}/n-${NMOL}/liquid-boxes.json" -o "${BOXES}/n-${NMOL}/runs-evaluator" -idx $SLURM_ARRAY_TASK_ID
fi



#!/usr/bin/env bash
#SBATCH -J simulate
#SBATCH --array=1-1%12
#SBATCH -p free-gpu
#SBATCH --gres=gpu:1
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account dmobley_lab_gpu
#SBATCH --output run-logs/slurm-%x.%A-%a.out

. ~/.bashrc

# Use the right conda environment
conda activate interchange-packmol-040

NMOL=1000
NEQ=100000
NPROD=1000000
TIMESTEP=2
NBAROSTAT=25

export OE_LICENSE=/data/homezvol3/lilyw7/oe_license.txt
export CUDA_VISIBLE_DEVICES=0

# get script path before changing directory
SCRIPT=$(readlink -m simulate.py)

# save the conda environment
conda env export > simulation-env.yaml

# figure out which directory to run in and go there
echo $SLURM_ARRAY_TASK_ID
PADDED_NUMBER=$(printf "%04d" $SLURM_ARRAY_TASK_ID)
ENTRY_NAME="entry-${PADDED_NUMBER}"
echo $ENTRY_NAME
OUTPUT_DIRECTORY="n-${NMOL}/runs/${ENTRY_NAME}"

mkdir -p $OUTPUT_DIRECTORY
cd $OUTPUT_DIRECTORY


# Run the commands
# only run if final file doesn't already exist
FINAL_FILE="ne-${NEQ}_np-${NPROD}_dt-${TIMESTEP}_nb-${NBAROSTAT}.pdb"
if [ ! -f $FINAL_FILE ]; then
    python $SCRIPT -i . -ne $NEQ -np $NPROD -dt $TIMESTEP -nb $NBAROSTAT
fi

echo "done"


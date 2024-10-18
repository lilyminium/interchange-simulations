#!/usr/bin/env bash
#SBATCH -J simulate-openmm-gpu
#SBATCH --array=1036-1036%300
#SBATCH -p free-gpu
#SBATCH --gres=gpu:1
#SBATCH -t 72:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account [xxx]
#SBATCH --output run-logs/slurm-%x.%A-%a.out

. ~/.bashrc

# Use the right conda environment
conda activate evaluator-0-4-10

BOXES="boxes-nosort"
NMOL=1000
# NEQ=100000
NEQ=1000000
NPROD=10000000
TIMESTEP=2
NBAROSTAT=25

export OE_LICENSE=[path/to/oe_license.txt]
export CUDA_VISIBLE_DEVICES=0

nvidia-smi

# get script path before changing directory
SCRIPT=$(readlink -m simulate-openmm-integrator-gpu.py)

# save the conda environment
conda env export > simulation-env.yaml

# figure out which directory to run in and go there
echo $SLURM_ARRAY_TASK_ID
PADDED_NUMBER=$(printf "%04d" $SLURM_ARRAY_TASK_ID)
ENTRY_NAME="entry-${PADDED_NUMBER}"
echo $ENTRY_NAME
OUTPUT_DIRECTORY="${BOXES}/n-${NMOL}/runs-interchange-final/${ENTRY_NAME}"

mkdir -p $OUTPUT_DIRECTORY
cd $OUTPUT_DIRECTORY

LIQUID_BOXES="../../liquid-boxes.json"


# Run the commands
# only run if final file doesn't already exist
FINAL_FILE="ne-${NEQ}_np-${NPROD}_dt-${TIMESTEP}_nb-${NBAROSTAT}.pdb"
if [ ! -f $FINAL_FILE ]; then
    python $SCRIPT -i . -ne $NEQ -np $NPROD -dt $TIMESTEP -nb $NBAROSTAT \
    -if $LIQUID_BOXES -idx $SLURM_ARRAY_TASK_ID -ip "input.pdb"
fi

echo "done"


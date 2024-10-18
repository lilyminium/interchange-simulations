#!/usr/bin/env bash
#SBATCH -J simulate-friction-coefficient
#SBATCH --array=1036-1036%30
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH -t 24:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account [xxx]
#SBATCH --output run-logs/slurm-%x.%A-%a.out

. ~/.bashrc

# Use the right conda environment
conda activate interchange-packmol-040-final

BOXES="boxes-nosort"
NMOL=1000
# NEQ=100000
NEQ=2500000
# NEQ=1000000
NPROD=1000000
# NPROD=1000000
TIMESTEP='2.0'
NBAROSTAT=25
FRICTION_COEFFICIENT='0.1'


export OE_LICENSE=[path/to/oe_license.txt]
export CUDA_VISIBLE_DEVICES=0

# get script path before changing directory
SCRIPT=$(readlink -m simulate-friction-coefficient.py)

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


# Run the commands
# only run if final file doesn't already exist
python $SCRIPT -i . -ne $NEQ -np $NPROD -dt $TIMESTEP -nb $NBAROSTAT -fc $FRICTION_COEFFICIENT

echo "done"


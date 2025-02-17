#!/bin/bash
# run: sbatch $HOME2/USP11/minimize.slurm.sh

#SBATCH --job-name=minimize
#SBATCH --chdir=/opt/xchem-fragalysis-2/mferla
#SBATCH --output=/opt/xchem-fragalysis-2/mferla/logs/slurm-error_%x_%j.log
#SBATCH --error=/opt/xchem-fragalysis-2/mferla/logs/slurm-error_%x_%j.log
#SBATCH --partition=main

#SBATCH --cpus-per-task=12
#SBATCH --priority=0

# -------------------------------------------------------

export SUBMITTER_HOST=$HOST
export HOST=$( hostname )
export USER=${USER:-$(users)}
export DATA=/opt/xchem-fragalysis-2
export HOME=$DATA/mferla
source /etc/os-release;

echo "Running $SLURM_JOB_NAME ($SLURM_JOB_ID) as $USER in $HOST which runs $PRETTY_NAME submitted from $SUBMITTER_HOST"
echo "Request had cpus=$SLURM_JOB_CPUS_PER_NODE mem=$SLURM_MEM_PER_NODE tasks=$SLURM_NTASKS jobID=$SLURM_JOB_ID partition=$SLURM_JOB_PARTITION jobName=$SLURM_JOB_NAME"
echo "Started at $SLURM_JOB_START_TIME"
echo "job_pid=$SLURM_TASK_PID job_gid=$SLURM_JOB_GID topology_addr=$SLURM_TOPOLOGY_ADDR home=$HOME cwd=$PWD"

# -------------------------------------------------------

source $HOME/waconda-slurm/etc/profile.d/conda.sh
conda activate base;

cd $HOME/dengue
python minimize.py

# -------------------------------------------------------

# Message details
JOB_NAME=${SLURM_JOB_NAME:-"Unknown Job"}
JOB_ID=${SLURM_JOBID:-"Unknown Job ID"}
HOST=$(hostname)
TIMESTAMP=$(date)

# Construct the message payload
MESSAGE=":tada: *SLURM Job Completed* :tada:\n*Job Name:* $JOB_NAME\n*Job ID:* $JOB_ID\n*Host:* $HOST\n*Time:* $TIMESTAMP"

# Send message to Slack
curl -s -o /dev/null -X POST -H 'Content-type: application/json' \
--data "{\"text\":\"$MESSAGE\"}" $SLACK_WEBHOOK
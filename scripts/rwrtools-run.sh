#!/bin/bash

set -x
set -e

export RWR_TOOLS_REPO=${RWR_TOOLS_REPO:-'/kb/module/RWRtools/'}
source /miniconda/etc/profile.d/conda.sh
conda activate rwrtools
mkdir -p /opt/work/tmp
cd $RWR_TOOLS_REPO
eval $RWR_TOOLS_COMMAND

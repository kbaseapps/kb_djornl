#!/bin/bash

set -e
set -x

export RWR_TOOLS_REPO=${RWR_TOOLS_REPO:-'/kb/module/RWRtools/'}
set +x
echo Activate rwrtools conda environment
source /miniconda/etc/profile.d/conda.sh
conda activate rwrtools
mkdir -p /opt/work/tmp
cd $RWR_TOOLS_REPO
R --no-restore --no-save << HEREDOC
devtools::install()
HEREDOC
set -x
eval $RWR_TOOLS_COMMAND

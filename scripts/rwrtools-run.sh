#!/bin/bash

set -x
set -e

export RWR_TOOLS_REPO=${RWR_TOOLS_REPO:-'/kb/module/RWRtools/'}
source /miniconda/etc/profile.d/conda.sh
conda activate rwrtools
mkdir -p /opt/work/tmp
cd $RWR_TOOLS_REPO
Rscript RWR_CV.R -h
exit 0 # stoppping here for now
echo Creating multiplex network
Rscript RWR_make_multiplex.R -v \
    -f ./data/network-flist-Athal.tsv \
    -o /opt/work/tmp/athal.Rdata
Rscript RWR_CV.R -v true \
    -d /opt/work/tmp/athal.Rdata \
    -g gold_sets/Athaliana/geneset_LeafSize.txt \
    -o /opt/work/tmp

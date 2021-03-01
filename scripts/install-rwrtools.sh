#!/bin/bash

set -x

export RWR_TOOLS_REPO=${RWR_TOOLS_REPO:-'.'}

conda env create -vv -f $RWR_TOOLS_REPO/environment.yml
source /miniconda/etc/profile.d/conda.sh
conda activate rwrtools
R --no-restore --no-save << HEREDOC
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager")
BiocManager::install("remotes")
BiocManager::install("dkainer/RandomWalkRestartMH")
HEREDOC
mkdir -p /opt/work/tmp
cd $RWR_TOOLS_REPO
Rscript RWR_CV.R -v true \
    -d ./multiplexes/Ptrichocarpa/mplex_Ptri_PENL_PENX_EXPAT_POPCYC_STRINGBIND_STRINGEXP_KO_DOM.Rdata \
    -g gold_sets/Ptrichocarpa/geneset_custom_GO-lignin.txt \
    -o /opt/work/tmp

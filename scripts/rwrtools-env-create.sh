#!/bin/bash

set -x
set -e

# source /miniconda/bin/activate
source /miniconda/etc/profile.d/conda.sh
#conda update -n base -c defaults conda
conda env create -v -f ./data/rwrtools.yml
conda activate rwrtools
R --no-restore --no-save << HEREDOC
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager")
BiocManager::install("remotes")
BiocManager::install("dkainer/RandomWalkRestartMH")
HEREDOC
# conda create --name rwrtools -c conda-forge r-base=4.0.2 r-devtools

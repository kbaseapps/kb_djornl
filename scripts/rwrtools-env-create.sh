#!/bin/bash

set -x
set -e

source /miniconda/etc/profile.d/conda.sh
conda env create -vv -f ./data/rwrtools.yml
conda activate rwrtools
R --no-restore --no-save << HEREDOC
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager")
BiocManager::install("remotes")
BiocManager::install("dkainer/RandomWalkRestartMH")
HEREDOC

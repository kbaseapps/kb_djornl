#!/bin/bash

set -x
set -e

source /miniconda/etc/profile.d/conda.sh
conda create -v -n rwrtools -c conda-forge r-base=4.0.2 r-devtools
conda activate rwrtools
git clone https://github.com/dkainer/RWRtoolkit.git
cd RWRtoolkit
R --no-restore --no-save << HEREDOC
devtools::install()
HEREDOC

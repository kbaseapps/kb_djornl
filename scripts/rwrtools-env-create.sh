#!/bin/bash

set -x
set -e

source /opt/conda3/etc/profile.d/conda.sh
conda create -v -n rwrtools \
    -c conda-forge r-base=4.3.3 r-devtools
conda activate rwrtools
git clone https://github.com/dkainer/RWRtoolkit.git
cd RWRtoolkit
# see also refdata-load.sh
git reset --hard 360f33794f7d81c254b7d8d16ef7649d0412f790
R --no-restore --no-save << HEREDOC
require(devtools)

# Matrix 1.7 depends on R >= 4.4
install_url("https://cran.r-project.org/src/contrib/Archive/Matrix/Matrix_1.6-5.tar.gz")
devtools::install()

HEREDOC

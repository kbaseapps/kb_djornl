#!/bin/bash

set -x
set -e

source /opt/conda3/etc/profile.d/conda.sh
conda create -v -n rwrtools \
    -c conda-forge r-base=4.1.0 r-devtools
conda activate rwrtools
git clone https://github.com/dkainer/RWRtoolkit.git
cd RWRtoolkit
# see also refdata-load.sh
git reset --hard 360f33794f7d81c254b7d8d16ef7649d0412f790
R --no-restore --no-save << HEREDOC
require(devtools)
install_version("igraph", version = "1.6.0", repos = "http://cran.us.r-project.org")
install_version("supraHex", version = "1.32.0", repos = "https://bioconductor.org/packages/3.14/bioc")
install_version("dnet", version = "1.1.7", repos = "http://cran.us.r-project.org")
devtools::install()

HEREDOC

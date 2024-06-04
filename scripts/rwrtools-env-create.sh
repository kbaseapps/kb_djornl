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
install_url("https://cran.r-project.org/src/contrib/Archive/Matrix/Matrix_1.6-5.tar.gz")
install_url("https://cran.r-project.org/src/contrib/Archive/MASS/MASS_7.3-60.0.1.tar.gz")
install_url("https://cran.r-project.org/src/contrib/Archive/igraph/igraph_1.6.0.tar.gz")
install_url("https://bioconductor.org/packages/3.14/bioc/src/contrib/supraHex_1.32.0.tar.gz")
install_url("https://cran.r-project.org/src/contrib/Archive/dnet/dnet_1.1.7.tar.gz")
devtools::install()

HEREDOC

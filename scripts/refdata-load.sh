#!/bin/bash
# Reference data initialization
set -x
set -e

# Retrieve static data exascale_data
git clone \
    https://github.com/kbase/exascale_data.git \
    /data/exascale_data
cd /data/exascale_data
git reset --hard 471e89d4f6aa1b9756b08e66aff3f9191d7dfe84
# Retrieve static data relation engine
git clone \
    https://github.com/kbase/relation_engine.git \
    /data/relation_engine
cd /data/relation_engine
git reset --hard 2a28213cc42c5ee566f17fb7bf46de38e5c17e4d
# Validate exascale_data using importers.djornl.parser
pip install -r /data/relation_engine/requirements.txt
PYTHONUNBUFFERED=yes RES_ROOT_DATA_PATH=/data/exascale_data/prerelease/ \
    python -m importers.djornl.parser --dry-run
# remove the database file if it exists
test -f /data/exascale_data/networks.db && rm /data/exascale/networks.db
/kb/module/scripts/networks_load.py
# Retrieve RWR tools and data
git clone https://github.com/dkainer/RWRtoolkit.git /data/RWRtools
cd /data/RWRtools
# see also rwrtools-env-create.sh
git reset --hard 360f33794f7d81c254b7d8d16ef7649d0412f790
git clone https://github.com/dkainer/RWRtoolkit-data.git /data/RWRtools/multiplexes
touch /data/__READY__

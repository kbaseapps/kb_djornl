#!/bin/bash
# Reference data initialization
set -x
set -e

# Retrieve static data relation engine
git clone --depth 1 \
    https://github.com/kbase/relation_engine.git \
    /data/relation_engine
# Retrieve static data exascale_data
git clone --depth 1 \
    https://github.com/kbase/exascale_data.git \
    /data/exascale_data
# Validate exascale_data using importers.djornl.parser
pip install -r /data/relation_engine/requirements.txt
cd /data/relation_engine
PYTHONUNBUFFERED=yes RES_ROOT_DATA_PATH=/data/exascale_data/prerelease/ \
    python -m importers.djornl.parser --dry-run
# remove the database file if it exists
test -f /data/exascale_data/networks.db && rm /data/exascale/networks.db
/kb/module/scripts/networks_load.py
# Retrieve RWR tools and data
git clone https://github.com/dkainer/RWRtoolkit.git /data/RWRtools
git clone https://github.com/dkainer/RWRtoolkit-data.git /data/RWRtools/multiplexes
touch /data/__READY__

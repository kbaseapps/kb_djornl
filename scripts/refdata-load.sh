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
# PYTHONUNBUFFERED=yes RES_ROOT_DATA_PATH=/data/exascale_data/prerelease/ \
#     python -m importers.djornl.parser --dry-run
# remove the database file if it exists
test -f /data/exascale_data/networks.db && rm /data/exascale/networks.db
/kb/module/scripts/networks_load.py
# Retrieve RWR tools and data
# /kb/module/scripts/rwrtools-env-create.sh
# Determine environment
KB_ENV=$(grep -e kbase_endpoint /kb/module/work/config.properties \
    | cut -f3 -d'/' | cut -f1 -d. \
)
# KB_ENV='appdev'
echo Detected environment $KB_ENV
if [[ "$KB_ENV" == 'kbase' ]]; then
    RWRTOOLS_BLOB_URL='https://kbase.us/services/shock-api/node/872033a7-2476-48e5-8ae0-afa2622376ab?download_raw'
elif [[ "$KB_ENV" == 'ci' ]]; then
    RWRTOOLS_BLOB_URL='https://ci.kbase.us/services/shock-api/node/c450f36f-c435-40c8-889e-2c43b1a4d270?download_raw';
elif [[ "$KB_ENV" == 'appdev' ]]; then
    RWRTOOLS_BLOB_URL='https://appdev.kbase.us/services/shock-api/node/403cef42-7e23-4160-a73f-0f3c26a878e5?download_raw';
fi
# Retrieve RWR tools and data
mkdir -p /data/RWRtools
curl -fsSL -H "Authorization: OAuth $KB_AUTH_TOKEN " \
  -o /data/RWRtools/RWRtools.tar.gz $RWRTOOLS_BLOB_URL
cd /data/RWRtools
tar xzvf RWRtools.tar.gz
source /miniconda/etc/profile.d/conda.sh
conda activate rwrtools
R --no-restore --no-save << HEREDOC
devtools::install()
HEREDOC
#devtools::install(args=-l /data/rwrp)
#bash /data/RWRtools/quickstart.sh
touch /data/__READY__

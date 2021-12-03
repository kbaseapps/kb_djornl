#!/bin/bash
# Reference data initialization
set -x
set -e
# Determine environment
KB_ENV=$(grep -e kbase_endpoint /kb/module/work/config.properties \
    | cut -f3 -d'/' | cut -f1 -d. \
)
echo Detected environment $KB_ENV
if [[ "$KB_ENV" == 'kbase' ]]; then
    RWRTOOLS_BLOB_URL='https://kbase.us/services/shock-api/node/e27516d4-e54d-4931-91f7-7d36c25fe3cc?download_raw'
elif [[ "$KB_ENV" == 'ci' ]]; then
    RWRTOOLS_BLOB_URL='https://ci.kbase.us/services/shock-api/node/0481bd3b-14b4-40f9-a585-aee531235edc?download_raw';
elif [[ "$KB_ENV" == 'appdev' ]]; then
    RWRTOOLS_BLOB_URL='https://appdev.kbase.us/services/shock-api/node/29d12bac-53b9-451f-8fc6-48124f1c2f8f?download_raw';
fi
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
# Retrieve RWR tools and data
mkdir -p /data/RWRtools
curl -fsSL -H "Authorization: OAuth $KB_AUTH_TOKEN " \
  -o /data/RWRtools/RWRtools.tar.gz $RWRTOOLS_BLOB_URL
cd /data/RWRtools
tar xzvf RWRtools.tar.gz
# remove the database file if it exists
test -f /data/exascale_data/networks.db && rm /data/exascale/networks.db
/kb/module/scripts/networks_load.py
touch /data/__READY__

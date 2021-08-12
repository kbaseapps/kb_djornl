# Reference data initialization
set -x
set -e
# Retrieve static data relation engine
git clone --depth 1 \
    https://github.com/kbase/relation_engine.git \
    --branch 2021-07-updates \
    /data/relation_engine
# Retrieve static data exascale_data
git clone --depth 1 \
    https://github.com/kbase/exascale_data.git \
    --branch 2021-07-updates \
    /data/exascale_data
# Validate exascale_data using importers.djornl.parser
pip install -r /data/relation_engine/requirements.txt
cd /data/relation_engine
PYTHONUNBUFFERED=yes RES_ROOT_DATA_PATH=/data/exascale_data/prerelease/ \
    python -m importers.djornl.parser --dry-run
# Retrieve RWR tools and data
mkdir -p /data/RWRtools
curl -H "Authorization: OAuth $KB_AUTH_TOKEN " \
  -o /data/RWRtools/RWRtools.tar.gz \
  https://ci.kbase.us/services/shock-api/node/8c05a5e1-f7b3-4458-ac57-efafc100d141?download_raw
cd /data/RWRtools
tar xzvf RWRtools.tar.gz
# remove the database file if it exists
test -f /data/exascale_data/networks.db && rm /data/exascale/networks.db
/kb/module/scripts/networks_load.py
touch /data/__READY__

#!/bin/bash

. /kb/deployment/user-env.sh

python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  make test
elif [ "${1}" = "async" ] ; then
  sh ./scripts/run_async.sh
elif [ "${1}" = "init" ] ; then
  echo "Initialize module"
  set -x
  set -e
  mkdir -p /data/RWRtools
  curl -H "Authorization: OAuth $KB_AUTH_TOKEN " \
    -o /data/RWRtools/RWRtools.tar.gz \
    https://ci.kbase.us/services/shock-api/node/0ce1edfb-949d-4ee4-9c58-ed8e40418200?download_raw
  cd /data/RWRtools
  tar xzvf RWRtools.tar.gz
  touch /data/__READY__
elif [ "${1}" = "bash" ] ; then
  bash
elif [ "${1}" = "report" ] ; then
  export KB_SDK_COMPILE_REPORT_FILE=./work/compile_report.json
  make compile
else
  echo Unknown
fi

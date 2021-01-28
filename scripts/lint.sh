#!/bin/sh

set -x

JS_FILES=$(git ls-files | grep -e ".js$")

echo "$JS_FILES" | xargs prettier --write
echo "$JS_FILES" | xargs eslint --fix

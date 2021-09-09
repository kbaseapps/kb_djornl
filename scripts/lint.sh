#!/bin/sh

set -e

BOLD="\033[1m"
CLEAR="\033[0m"
function hint_fix {
    echo <<HINT
Run \`${BOLD}npm run fix$CLEAR\` to attempt an automatic fix to this problem.
HINT
}
trap hint_fix ERR

if [[ -z $CHECK ]]
then
WRITE="--write"
FIX="--fix"
fi
JS_FILES=$(git ls-files | grep -e ".js$")

echo "$JS_FILES" | xargs prettier $CHECK $WRITE
echo "$JS_FILES" | xargs eslint $FIX --max-warnings=0

python -m black $CHECK -v \
	lib/kb_djornl/__init__.py \
	lib/kb_djornl/utils.py \
	scripts/postinstall.py \
	test

#!/bin/sh
# Validate the conventional commits specification is respected

# skip merge commits
git rev-parse -q --verify MERGE_HEAD && exit 0

RED="\033[0;31m"
GREEN="\033[0;92m"
NC="\033[0m"

INPUT_FILE=$1
COMMIT_MSG=$(head -n1 $INPUT_FILE)

CC_TYPES="build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test"
CC_SCOPE="\([a-zA-Z]+\)"
PATTERN="(${CC_TYPES})($CC_SCOPE)?[!]?: [a-zA-Z].+"

if [[ ! $COMMIT_MSG =~ $PATTERN ]]; then
    echo "${RED}✖${NC} Conventional Commits specification not respected
ⓘ Official specification: https://www.conventionalcommits.org/en/v1.0.0/

Commit message must respect the following format:
<type>(<optional scope>): <description>

Supported types are: ${CC_TYPES}
Commit message with ! to draw attention to breaking change

Examples:
- feat: allow provided config object to extend other configs
- refactor!: drop support for python 3.7
- docs: correct spelling of CHANGELOG
- feat(lang): add polish language
"
    exit 1
fi

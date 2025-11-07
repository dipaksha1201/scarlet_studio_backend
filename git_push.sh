#!/bin/bash
# Simple helper to add, commit, and push. Configure GIT_REMOTE before use.
set -e
GIT_REMOTE=${GIT_REMOTE:-origin}
BRANCH=${BRANCH:-main}
git add .
git commit -m "${1:-'update assessment designer'}" || echo "nothing to commit"
git push "$GIT_REMOTE" "$BRANCH"
echo "Pushed to $GIT_REMOTE/$BRANCH (ensure remote is configured)"


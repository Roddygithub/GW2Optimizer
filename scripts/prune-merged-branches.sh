#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REMOTE="origin"

remote="${1:-$DEFAULT_REMOTE}"
echo "# Branches merges dans ${remote}/main (hors main, HEAD, release/*)" >&2

git fetch "$remote" --prune

branches=$(git branch -r --merged "${remote}/main" | grep -vE "${remote}/main|${remote}/HEAD|${remote}/release/" | sed "s#${remote}/##")

if [ -z "$branches" ]; then
  echo "# Aucune branche mergée à pruner" >&2
  exit 0
fi

while IFS= read -r branch; do
  if [ -n "$branch" ]; then
    echo "git push ${remote} --delete ${branch}"
  fi
done <<< "$branches"

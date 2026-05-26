#!/bin/bash
set -e

# Usage: ./scripts/ship.sh "feat: description of change"
#
# Creates a branch named after the description, commits all staged/unstaged
# changes, pushes, and opens a PR on GitHub.
#
# Examples:
#   ./scripts/ship.sh "feat: section-aware chunking"
#   ./scripts/ship.sh "experiment: chunking strategy comparison"
#   ./scripts/ship.sh "fix: section regex not matching multi-line headers"

DESCRIPTION="${1:-}"

if [ -z "$DESCRIPTION" ]; then
  echo "Error: provide a description."
  echo "Usage: ./scripts/ship.sh \"feat: your change description\""
  exit 1
fi

# Derive a branch slug from the description.
# "feat: section-aware chunking" -> "feat/section-aware-chunking"
PREFIX=$(echo "$DESCRIPTION" | sed 's/:.*//')   # everything before the colon
SUFFIX=$(echo "$DESCRIPTION" | sed 's/^[^:]*: *//')  # everything after "type: "
SLUG=$(echo "$SUFFIX" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
BRANCH="mason/${PREFIX}/${SLUG}"

echo "Branch: $BRANCH"

# Make sure we branch off of an up-to-date main.
git checkout main
git pull origin main
git checkout -b "$BRANCH"

echo "Staging changes..."
git add .

if git diff --cached --quiet; then
  echo "Nothing to commit. Make some changes first."
  git checkout main
  git branch -d "$BRANCH"
  exit 1
fi

git commit -m "$DESCRIPTION"

echo "Pushing..."
git push origin "$BRANCH"

echo "Opening PR..."
gh pr create \
  --title "$DESCRIPTION" \
  --body "" \
  --base main \
  --head "$BRANCH"

echo "Done."

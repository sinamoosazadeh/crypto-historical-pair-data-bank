#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

OWNER="sinamoosazadeh"
REPO="crypto-historical-pair-data-bank"
DESCRIPTION="Evidence-first catalogue and tools for historical cryptocurrency pair market data"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f README.md || ! -f catalog/sources.json || ! -f index.html ]]; then
  echo "ERROR: Run this script from the prepared project package." >&2
  exit 2
fi
if ! command -v git >/dev/null 2>&1 || ! command -v gh >/dev/null 2>&1; then
  echo "Install dependencies first: pkg install git gh python" >&2
  exit 2
fi

python scripts/build_catalog.py
python scripts/build_manifest.py
python scripts/check_english_only.py
python scripts/validate_catalog.py
python -m compileall -q scripts tests
if command -v node >/dev/null 2>&1; then node --check web/assets/app.js; fi
python -m unittest discover -s tests -v

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. The token is read invisibly and never added to this repo."
  echo "It must allow repository creation, content pushes (including workflow files), and Pages administration."
  echo "For a classic personal access token, the usual required scopes are repo and workflow."
  IFS= read -r -s -p "Paste your GitHub token here in Termux (never into ChatGPT): " GH_TOKEN
  printf '\n'
  if [[ -z "${GH_TOKEN}" ]]; then echo "Empty token; aborting." >&2; exit 3; fi
  printf '%s\n' "$GH_TOKEN" | gh auth login --with-token
  unset GH_TOKEN
fi

REPO_EXISTS=0
REMOTE_URL="https://github.com/$OWNER/$REPO.git"
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  REPO_EXISTS=1
  if git ls-remote --heads "$REMOTE_URL" 2>/dev/null | grep -q .; then
    echo "ERROR: $OWNER/$REPO already has one or more branches." >&2
    echo "Refusing to overwrite or merge an existing history automatically." >&2
    echo "Clone the existing repository and reconcile the project deliberately." >&2
    exit 4
  fi
  echo "Found an existing empty repository; it is safe to publish the prepared first commit."
fi

if [[ ! -d .git ]]; then git init -b main; fi
# Git identity falls back to the authenticated GitHub login; no email address is exposed.
if ! git config user.name >/dev/null; then
  GH_LOGIN="$(gh api user --jq .login)"
  git config --local user.name "$GH_LOGIN"
fi
if ! git config user.email >/dev/null; then
  GH_LOGIN="$(gh api user --jq .login)"
  git config --local user.email "${GH_LOGIN}@users.noreply.github.com"
fi
# Do not stage secret-like files even if added locally by accident.
git add -A
if git diff --cached --quiet; then
  echo "No staged changes to publish." >&2
  exit 5
fi

git commit -m "Initial release: historical crypto-pair data catalogue"
if [[ "$REPO_EXISTS" -eq 1 ]]; then
  git remote add origin "$REMOTE_URL"
else
  gh repo create "$OWNER/$REPO" --public --description "$DESCRIPTION" --source . --remote origin
fi
git push -u origin main
# Configure Pages only after the first branch exists; GitHub can reject this endpoint on an empty repo.
# If account policy blocks the API action, enable Pages once at Settings > Pages > Build and deployment > GitHub Actions.
if gh api --method POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1; then
  echo "GitHub Pages configured for workflow deployment."
else
  echo "NOTICE: Could not enable GitHub Pages automatically; use Settings > Pages > Source > GitHub Actions."
fi
gh repo edit "$OWNER/$REPO" \
  --add-topic crypto \
  --add-topic cryptocurrency \
  --add-topic historical-data \
  --add-topic crypto-data \
  --add-topic market-data \
  --add-topic open-data \
  --add-topic dataset \
  --add-topic data-engineering

echo
echo "Repository created and pushed: https://github.com/$OWNER/$REPO"
echo "Next: inspect the Actions tab; Pages may need a one-time source setting depending on account policy."

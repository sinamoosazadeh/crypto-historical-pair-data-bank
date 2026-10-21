# Publishing from an authenticated local Git environment (optional)

This is an optional fallback for maintainers who prefer a local Git push. It is not required to inspect or test the static site. Use GitHub CLI or Git credentials that are already authenticated locally. Never paste a personal access token into a chat, terminal command, source file, issue, or commit.

## Target repository

- Repository name: `crypto-historical-pair-data-bank`
- Intended owner: `sinamoosazadeh`
- Intended visibility: public, so the catalogue and GitHub Pages can be discovered.
- Default branch: `main`

The publish helper can create the public repository when the slug does not exist. If you create it manually instead, leave it empty: do not initialize a README, license, or `.gitignore` remotely. The helper can attach to an existing repository only when it has no branches; it refuses to overwrite or silently merge an existing history.

The script `scripts/termux_publish.sh` checks local tool/authentication prerequisites before proceeding. Review it before execution. It must not receive a token as a command-line argument or write credentials into the repository. If the GitHub CLI is not authenticated, it reads the token through hidden terminal input. The credential must permit repository creation, pushing repository contents (including GitHub Actions workflow files), and Pages administration; a classic personal access token typically needs the `repo` and `workflow` scopes. Never paste the token into ChatGPT.

## After the initial push

1. Confirm the CI workflow is green.
2. Enable GitHub Pages with the GitHub Actions deployment source if it is not already enabled.
3. Confirm the generated site, catalog downloads, and workflows work from the repository URL.
4. Check the Actions permissions and Pages deployment environment.
5. Add the first release only after the inventory claims, source links, and snapshot date have been reviewed.


## Check before publishing

The archive is designed to contain English-only text and generated catalogue metadata. The initial source snapshot is not a live full-history download audit. Run `python scripts/check_english_only.py`, `python scripts/validate_catalog.py`, and the complete unit test suite before the first push. The publish helper does not overwrite an existing non-empty GitHub repository. If the slug already exists with branches, it exits safely and requires a deliberate recovery workflow. An existing branchless repository can be used for the initial push.

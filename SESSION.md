# SESSION.md

## Current milestone
**Next.js marketing and documentation site for GitHub Pages**

## Current branch
`feat/nextjs-pages-site`

## PR
To be opened with gh after final checks.

## Last completed step
- PR #103 merged; headless API container workflow published successfully to GHCR on main. The Windows desktop distribution remains separate.
- Next.js 16 static export built in `site/` for `https://mdaashir.github.io/kural/` with product landing page, downloads, documentation (quickstart, commands, configuration, API, troubleshooting), local artwork, canonical metadata, sitemap and robots.
- `.github/workflows/pages.yml` builds on PR and deploys only from main/manual main to `github-pages` using Pages/OIDC permissions. Site links point to existing v0.1.3 GitHub Release and PyPI package; no site deployment has occurred.

## Verification
- `npm ci`, `npm run typecheck`, `npm run lint`, `npm run build`, `npm test` passed; 4 export tests verify Pages base-path links and static assets.
- Python Ruff lint/format passed (144 files); `pytest -q`: 590 passed. Hosted Pages/CI checks remain pending until PR.
- Visual browser gate in design-taste-frontend skill was unavailable (script runner reported `scripts/gate.mjs` missing); no browser screenshots were checked.

## Next steps
1. Verify repository tests, Pages workflow syntax, and site links; review diff.
2. Commit, push and open one focused site PR; inspect hosted Pages build and Python CI.
3. Wait for user review/merge; configure GitHub Pages source to **GitHub Actions** if not already set, then verify deployment and live links.
4. Docker Hub is deferred. GHCR uses GitHub token; Docker Hub publishing requires Docker Hub credentials or a supported trusted-publishing integration, not the GitHub token alone.

## Open limitations
- No live GitHub Pages deployment or browser layout screenshots yet. GPU/microphone/live desktop behavior is not exercised by site tests.

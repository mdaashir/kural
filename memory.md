# Memory — Next.js GitHub Pages marketing/docs site

Last updated: 2026-11-21

## Current state
- `cmd-kural==0.1.3` is published on PyPI and v0.1.3 GitHub Release assets/checksums were verified.
- PR #103 merged; headless API image is published by GitHub Actions to `ghcr.io/mdaashir/kural`. Container API is separate from the Windows desktop app and has no built-in authentication; Compose binds its port to host loopback only.
- Working branch: `feat/nextjs-pages-site`. Building a Next.js static-export site for `https://mdaashir.github.io/kural/`, with product landing, verified download links, user/developer docs, local artwork, and SEO metadata.

## Decisions
- Site has no analytics, cloud inference, runtime server or invented testimonials/benchmarks. It explains the one-time model download and Windows desktop focus.
- GitHub Pages deploy workflow runs PR build checks without deploying; main-only deployments use `github-pages` environment and GitHub Pages token/OIDC permissions. Site uses `basePath: /kural` and static export.
- Docker Hub is deferred. The GHCR workflow uses `GITHUB_TOKEN`; Docker Hub is a separate service and cannot be assumed to accept that token.

## Verification and limitations
- `npm ci`, Next.js typecheck/lint/build, and four static-export tests passed locally.
- Python Ruff lint/format passed (144 files); pytest: 590 passed. Hosted Pages/CI checks pending PR. Site is not deployed yet.
- The design-taste-frontend gate script was unavailable from the skill runner, so responsive browser screenshots were not verified. No live microphone/GPU validation is part of site tests.

## Next step
Finish Pages workflow and docs review, run full gates, open one PR, wait for merge, then configure Pages source to GitHub Actions and verify live deployment. Docker Hub publishing remains a separate follow-up.

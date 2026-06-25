# Handover: Deploy Polkadot Docs to GitHub Pages (safety-net)

> **For: Claude Code, running on Reinhard's filesystem.**
> You have no memory of the conversation that produced this brief. Everything you need is below. Read the whole document before acting. Ask before any irreversible or account-level change (DNS cutover, deleting infra).

---

## 1. Mission

Take over `https://docs.polkadot.com` from the outgoing provider (PaperMoon) **before their hard cutoff of June 30, 2026** (≈6 days from June 24). Their production build-and-publish process and their AWS hosting disappear at cutoff.

**Your immediate goal:** stand up a working GitHub Pages deployment of the docs so the site cannot go dark on June 30. This is the *safety net*, not the final home.

**The eventual production target is Cloudflare Pages** (full parity: unlimited bandwidth, server-side redirects, security headers). The DNS is already on Cloudflare. So: build everything in a way that also serves the Cloudflare migration, but get GitHub Pages live first.

Do **not** over-engineer. Do **not** repoint DNS until the GitHub Pages build is verified working on the `*.github.io` URL.

---

## 2. What the site is (verified facts)

The docs are a **MkDocs + Material static site**. The output is 100% static; nothing needs a server at request time. Verified by a full local build:

| Fact | Value |
|---|---|
| Build command | `mkdocs build --strict` (wrapped by `make build`) |
| Python | 3.10+ (3.12 verified working) |
| System libs needed | Cairo/Pango for social-card imaging (`mkdocs-material[imaging]`) |
| Build time | ~120 s (well under GitHub Pages' 10-min deploy timeout) |
| Output size | 274 MB / 1,019 files (under GH Pages' 1 GB site limit) |
| Social cards | 233 PNGs = 167 MB (61% of output) |
| `site_url` | `https://docs.polkadot.com/` — **unchanged**, so no canonical/sitemap rewrites |
| Redirects | **267 entries** in `redirects.json` |

**Two repos, nested at build time:**
- **Framework repo:** `papermoonio/polkadot-mkdocs` — holds `mkdocs.yml`, theme overrides, `hooks/`, plugin config, `redirects.json`, `llms_config.json`, `requirements.txt`, `Makefile`. *(Ownership/fork must be sorted by Parity — confirm where the deploy lives. See §6.)*
- **Content repo:** `polkadot-developers/polkadot-docs` — the actual markdown. It is checked out **into the framework repo as `polkadot-docs/`** for the build. The `macros` plugin reads `polkadot-docs/variables.yml`.

**Plugins/hooks (all build-time, all portable):** `search`, `ai_docs`, `awesome-nav`, `git-revision-date-localized`, `glightbox`, `link_processor`, `macros`, `minify`, `social`, plus `hooks/auto_index_table.py`, `footer_nav.py`, `glossary_abbreviations.py`, `synthesize_ancestors.py`. The "AI page actions" dropdown (`ai_docs` + `js/ai-file-actions.js`) is fully client-side: it `fetch()`es the static resolved `.md` files same-origin. No backend.

---

## 3. The two things GitHub Pages does NOT inherit

The current production behaviour relies on **CloudFront**, not the repo. Neither of these is emitted by the build — verified:

1. **267 redirects.** `redirects.json` is the source of truth, but it is **not wired into MkDocs** (`mkdocs-redirects` is installed yet unconfigured; the build emits zero redirect stubs). On GitHub Pages these old URLs will 404 unless we generate them. → **You must generate client-side redirect stubs.** (On Cloudflare later, use a real `_redirects` file instead.)
2. **Security headers.** CloudFront injects `content-security-policy`, `strict-transport-security`, `x-content-type-options`, `x-frame-options`, `x-xss-protection`, `referrer-policy`, `cross-origin-opener-policy`. **GitHub Pages emits none of these and cannot be configured to** (confirmed: `polkadot.com`, itself on GitHub Pages, returns only `server: GitHub.com`). This is an accepted trade-off for the short-term net. The production Cloudflare Pages target restores them via a `_headers` file. Do not block the GitHub Pages deploy on this.

---

## 4. Host context (so you understand the landscape)

- **DNS:** the `polkadot.com` zone is on **Cloudflare** (nameservers `*.ns.cloudflare.com`), used **DNS-only (grey cloud)** — Cloudflare is not in the request path. Repointing `docs` is a single Cloudflare DNS change.
- **`docs.polkadot.com` today:** AWS CloudFront + S3 (PaperMoon's account), gone at cutoff.
- **`polkadot.com` today:** a **statically-exported Next.js site on GitHub Pages** (`server: GitHub.com`, `via: varnish`), Cloudflare DNS-only in front. **This proves GitHub Pages is already an org-sanctioned host for an official polkadot.com property.** Its existing Pages workflow is the pattern to mirror — find and reuse it.

---

## 5. Step 0 — Orient (do this first)

The local dir `/Users/reinhard/projects/polkadotcom` holds "the polkadot.com sites." Before changing anything:

1. `ls`/inspect that directory. Identify what's present: the Next.js `polkadot.com` site, and **whether the docs repos (`polkadot-mkdocs` and/or `polkadot-docs`) are already cloned**.
2. **Find the existing GitHub Pages workflow** used by `polkadot.com` (look in `.github/workflows/`). Read it — mirror its conventions (runner, permissions, action versions, deploy method) in what you write below.
3. If the docs repos are absent, clone them into a working location:
   ```bash
   git clone https://github.com/papermoonio/polkadot-mkdocs.git
   cd polkadot-mkdocs
   git clone https://github.com/polkadot-developers/polkadot-docs.git polkadot-docs
   ```
4. **Confirm the framework repo's default/production branch** (the handover materials reference both `main` and `master` across repos). The deploy workflow trigger and content checkout must match reality.

---

## 6. Open questions — ask Reinhard before finalizing

- **Which repo/org owns the deploy?** The CNAME target is `<owner>.github.io`, so this must be settled. Candidates: a Parity/`paritytech` fork of `polkadot-mkdocs`, `polkadot-developers`, or wherever the org wants it. Do not assume.
- **Is the deploy repo public or private?** Public is fine on any plan; private Pages requires an appropriate org plan.
- **OK to use client-side (meta-refresh) redirects for the stopgap?** (Yes is expected — it's the only option on GitHub Pages. Real 301s come with the Cloudflare migration.)

---

## 7. Tasks you can do on the filesystem

### 7.1 Reproduce the build locally (sanity check)
```bash
# from inside the framework repo, with polkadot-docs/ checked out inside it
brew install cairo pango gdk-pixbuf libffi   # macOS equivalent of the Linux imaging libs
python3 -m venv venv && ./venv/bin/pip install -U pip
./venv/bin/pip install -r requirements.txt
./venv/bin/mkdocs build --strict -d site     # or: make build
```
> **Gotcha:** `--strict` + `git-revision-date-localized` require the **content repo's full git history**. A shallow clone makes the build fail under `--strict`. Ensure `polkadot-docs/` has full history locally, and `fetch-depth: 0` in CI (see workflow). If `--strict` fails only on pre-existing link warnings unrelated to migration, flag it; do not silently drop `--strict` without telling Reinhard.

### 7.2 Add a redirect generator — `scripts/gen_redirects.py`
This serves **both** the GitHub Pages stopgap (`stubs`) and the Cloudflare production target (`cloudflare`), from the single source of truth `redirects.json` (267 entries):

```python
#!/usr/bin/env python3
"""Generate redirects from redirects.json.
  --format stubs       -> <site>/<old>/index.html meta-refresh stubs (GitHub Pages)
  --format cloudflare  -> <site>/_redirects with real 301s (Cloudflare Pages / Netlify)
Never clobbers a real built page.
"""
import argparse, json, os, html

def load(path):
    with open(path) as f:
        return json.load(f)["data"]

def lead_slash(p):
    return p if p.startswith("/") else "/" + p

def write_stubs(entries, site_dir):
    written = skipped = 0
    for e in entries:
        old = lead_slash(e["key"]).strip("/")
        new = html.escape(lead_slash(e["value"]))
        out_dir = os.path.join(site_dir, old)
        index = os.path.join(out_dir, "index.html")
        if os.path.exists(index):        # real page wins; never overwrite
            skipped += 1
            continue
        os.makedirs(out_dir, exist_ok=True)
        with open(index, "w") as f:
            f.write(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<title>Redirecting…</title>'
                f'<meta http-equiv="refresh" content="0; url={new}">'
                f'<link rel="canonical" href="{new}">'
                '<meta name="robots" content="noindex">'
                f'<script>location.replace("{new}")</script></head>'
                f'<body>Redirecting to <a href="{new}">{new}</a></body></html>'
            )
        written += 1
    print(f"stubs: wrote {written}, skipped {skipped} (real pages)")

def write_cloudflare(entries, site_dir):
    lines = [f"{lead_slash(e['key'])}  {lead_slash(e['value'])}  301" for e in entries]
    with open(os.path.join(site_dir, "_redirects"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"cloudflare: wrote {len(lines)} rules to {site_dir}/_redirects")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["stubs", "cloudflare"], required=True)
    ap.add_argument("--site-dir", default="site")
    ap.add_argument("--redirects", default="redirects.json")
    a = ap.parse_args()
    entries = load(a.redirects)
    (write_stubs if a.format == "stubs" else write_cloudflare)(entries, a.site_dir)
```

### 7.3 Add the deploy workflow — `.github/workflows/deploy-pages.yml`
Adapt to mirror polkadot.com's existing workflow (action versions, runner) where it differs. Replace the `BRANCH` and the content `repository` if §5/§6 revealed different values.

```yaml
name: Deploy docs to GitHub Pages

on:
  push:
    branches: [main]        # <-- confirm framework repo's production branch (§5.4)
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout framework repo
        uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - name: Checkout content repo into polkadot-docs/
        uses: actions/checkout@v4
        with:
          repository: polkadot-developers/polkadot-docs   # <-- confirm
          path: polkadot-docs
          fetch-depth: 0       # full history: required for git-revision-date under --strict

      - name: Install imaging libs (social cards)
        run: |
          sudo apt-get update
          sudo apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.12' }

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Build site
        run: mkdocs build --strict -d site

      - name: Generate client-side redirect stubs (GH Pages has no server-side 301s)
        run: python scripts/gen_redirects.py --format stubs --site-dir site --redirects redirects.json

      - name: Custom domain
        run: echo "docs.polkadot.com" > site/CNAME

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with: { path: site }

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

> If the framework repo already contains the handover's `deploy-docs.yml`, reconcile with it rather than duplicating — keep one workflow.

### 7.4 Local verification before any push
```bash
mkdocs build --strict -d site
python scripts/gen_redirects.py --format stubs --site-dir site
python -m http.server -d site 8080
# then check: homepage loads; a known redirect resolves, e.g.
#   /chain-interactions/accounts/  ->  /chain-interactions/accounts/create-account/
# check: search works; an AI "copy as markdown" action fetches /<page>.md (200)
```

---

## 8. Steps that need GitHub/Cloudflare (Reinhard, or you via `gh`)

These are **not** filesystem edits — flag them clearly and offer to run the `gh` ones:

1. **Enable Pages:** repo → Settings → Pages → **Source = GitHub Actions** (not "deploy from a branch"; no `gh-pages` branch). Via CLI: `gh api -X POST repos/<owner>/<repo>/pages -f build_type=workflow` (verify against current `gh` API).
2. **Custom domain + HTTPS:** set `docs.polkadot.com`, tick **Enforce HTTPS** (the workflow already writes `site/CNAME`).
3. **Cloudflare DNS (do LAST, after verifying the `*.github.io` URL):** add `docs` CNAME → `<owner>.github.io`, **grey cloud (DNS-only)**. This is the cutover. The current CloudFront site stays live until this record flips.

---

## 9. Acceptance checklist (stopgap is "done" when)

- [ ] Workflow builds green; deploy job publishes to the `*.github.io` URL.
- [ ] Output is ~270–280 MB / ~1,000+ files; build < 10 min.
- [ ] Homepage, a deep reference page, search, and the AI "copy/view markdown" actions all work on the `*.github.io` URL.
- [ ] At least 5 sampled entries from `redirects.json` resolve to their targets.
- [ ] `CNAME` present in the published site.
- [ ] **Only then:** Cloudflare DNS repointed; `docs.polkadot.com` serves from GitHub Pages (`server: GitHub.com`); spot-check redirects + key pages on the real domain.

---

## 10. Out of scope here (track separately, also due ~June 30)

These are **not hosting** and won't be fixed by this deploy — surface them, don't try to solve them in the workflow:

- **`requirements.txt` is not pinned in-repo** — it `-r`'s a remote, mutable file (`papermoonio/workflows@main`). Vendor/pin it on takeover. The resolved set includes `papermoon-mkdocs-plugins==0.1.0a18` (an *alpha* of a package flagged as unmaintained).
- **Third-party accounts** embedded client-side: **Kapa AI** (chatbot, `data-website-id`) and **Google Analytics** (the "Was this page helpful?" feedback). Ownership/credentials must transfer or these break/lose data at cutoff.
- **MCP endpoint** `docs-mcp.polkadot.com` currently fronts PaperMoon's AWS ALB; it dies at cutoff unless self-hosted or the records are confirmed under Parity control.

---

## 11. After the net is up: the real production target

Once GitHub Pages is live and safe, the recommended permanent home is **Cloudflare Pages** (free tier: unlimited bandwidth, commercial use allowed, DNS already on Cloudflare). It restores full parity with today:
- redirects → `python scripts/gen_redirects.py --format cloudflare` (real 301s via `_redirects`)
- security headers → a `_headers` file reproducing the CloudFront CSP/HSTS/etc.
- `.md` files → ensure served as `text/plain` inline (for the "view as markdown" action).

Ask Reinhard whether to proceed to Cloudflare Pages once the GitHub Pages safety net is confirmed.

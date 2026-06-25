# Polkadot Documentation & MCP Server \- Handover

**Date:** 2026/06/23   
**Scope:** Hosting and operation of the Polkadot Developer Documentation and the documentation MCP server.

This document provides an overview of how the Polkadot developer documentation is built and published, how the documentation MCP server is hosted and run, and the framework-repo internals that a maintainer needs to operate it day-to-day. Sections 1-2 are an orientation for the Parity team taking ownership; section 3 is the maintenance reference for `polkadot-mkdocs`.

For content-authoring conventions (how to add a page, frontmatter fields, navigation files, snippets, images, callouts, style rules), see the [**`CONTRIBUTING.md`](https://github.com/polkadot-developers/polkadot-docs/blob/master/CONTRIBUTING.md)** in the `polkadot-docs` content repo. This handover does not duplicate that guide; it focuses on the framework, build/publish pipeline, and the MCP server.

Open topics:

- [ ] [Policies](https://docs.polkadot.com/policies/terms-of-use/)  
- [ ] Analytics \- Our own Google Analytics that is linked to the “Was this page helpful?” feature.   
- [ ] Redirects \- Server side (Cloudflare)(better SEO) or client side (Mkdocs feature)(Simpler)  
- [ ] MCP Handover  
- [ ] Docs Hosting

---

## 1\. Scope

This handover covers the **documentation** \- its content and the framework/theme used to build and publish it \- and **guidance for running the documentation MCP server**.

| Component | Repository | Org today | Status |
| ----- | ----- | ----- | ----- |
| [Documentation content](https://github.com/polkadot-developers/polkadot-docs) | `polkadot-developers/polkadot-docs` | polkadot-developers | Handed over (already in target org) |
| [Tested code examples](https://github.com/polkadot-developers/polkadot-cookbook) | `polkadot-developers/polkadot-cookbook` | polkadot-developers | Handed over (already in target org) |
| [Docs framework & theme](https://github.com/papermoonio/polkadot-mkdocs) | `papermoonio/polkadot-mkdocs` | papermoonio | Handed over |
| [MkDocs plugins](https://github.com/papermoonio/mkdocs-plugins) | `papermoonio/mkdocs-plugins` | papermoonio | **Not handed over** \- open-source tool used by the docs |
| [MCP server](https://github.com/papermoonio/mkdocs-mcp) | `papermoonio/mkdocs-mcp` | papermoonio | **Not handed over** \- open-source tool available for Parity to use |

Two of these are general-purpose, open-source PaperMoon tools published on PyPI and are **not** part of the transfer. Parity is free to use them as-is:

- **`papermoon-mkdocs-plugins`** \- a collection of custom MkDocs plugins that the docs build depend on (see Section 2.6).  
- **`papermoon-mkdocs-mcp`** \- the MkDocs MCP server that powers the current docs MCP endpoint (see Section 4).

The published outputs are:

- **Docs site:** [https://docs.polkadot.com/](https://docs.polkadot.com/)  
- **MCP endpoint (current, PaperMoon-hosted):** [https://mkdocs-mcp.papermoon.io/polkadot/mcp](https://mkdocs-mcp.papermoon.io/polkadot/mcp)

---

## 2\. Documentation

### 2.1 Two-repository structure

The documentation is split across **two repositories**:

1. **Content** lives in `polkadot-developers/polkadot-docs` \- just the Markdown, images, snippets, and navigation files. It is already in the polkadot-developers org.  
2. **Framework** lives in `papermoonio/polkadot-mkdocs` \- this holds `mkdocs.yml`, the Material for MkDocs theme overrides, custom CSS/JS, redirects, hooks, and the build tooling. It contains **no documentation content**.

At build time (locally or in CI), the content repo is cloned *into* the framework repo, so the directory layout looks like this:

```
polkadot-mkdocs/
├── material-overrides/      # theme overrides
├── hooks/                   # build-pipeline hooks
├── layouts/                 # social-card layout
├── policies/                # legal pages
├── polkadot-docs/           # content repo, cloned in
└── mkdocs.yml               # points docs_dir at polkadot-docs/
```

`mkdocs.yml` sets `docs_dir: polkadot-docs` so MkDocs reads content from the cloned-in repo. The stack is [**MkDocs**](https://www.mkdocs.org/) with the [**Material for MkDocs**](https://squidfunk.github.io/mkdocs-material/) theme.

### 2.2 Local development

**Prerequisites:**

- Python 3.10+  
- `make` (macOS/Linux) or the equivalent commands from `Makefile.bat` on Windows  
- A local clone of `polkadot-docs` inside the framework repo:

```shell
git clone https://github.com/polkadot-developers/polkadot-docs.git polkadot-docs
```

**Commands** (run from inside `polkadot-mkdocs`):

| Command | What it does |
| ----- | ----- |
| `make install` | Creates a `venv/` virtual environment and installs all dependencies from `requirements.txt` |
| `make reinstall` | Force-reinstalls all dependencies (use when `requirements.txt` changes) |
| `make serve` | Starts a local dev server at [http://127.0.0.1:8000](http://127.0.0.1:8000) with live reload |
| `make build` | Builds the static site with `--strict` (fails on warnings/broken links \- mirrors CI) |

Pass extra MkDocs flags via `ARGS`, e.g., `make serve ARGS='--watch-theme'`. The `make serve`/`make build` targets create the virtualenv and install dependencies automatically on first run.

`venv/` (local environment) and `site/` (build output) are not committed. `.cache/` holds Material's generated social cards between builds and is safe to delete to force a full rebuild.

### 2.3 How it is published

Production at [https://docs.polkadot.com/](https://docs.polkadot.com/) is published by an **internal PaperMoon build process**, not by a GitHub Actions workflow. At a high level, it periodically checks the framework repo (`papermoonio/polkadot-mkdocs`) and the content repo (`polkadot-developers/polkadot-docs`) for new commits, rebuilds the static site with MkDocs when either repo has changed (content is cloned into the framework repo, as in Section 2.1), and serves the result. In practice, this means merging to the tracked branch of either repo is all that is needed to publish \- changes go live automatically a short time later, with no manual deploy step.

The internal publishing mechanics are PaperMoon-specific and are not part of this handover. **Parity is expected to implement its own publishing logic** \- any build-and-serve pipeline that produces the MkDocs static site (`make build`, see Section 2.2) and hosts it at the target domain is sufficient. The docs themselves do not depend on how they are deployed.

**Fallback path \- `deploy-docs.yml`.** The `papermoonio/polkadot-mkdocs` repo also contains a **`Deploy Docs`** GitHub Actions workflow (`.github/workflows/deploy-docs.yml`) that deploys to **GitHub Pages**. This is *not* how production is published; it exists as a manual fallback/staging path and can serve as a starting reference for Parity's own pipeline. It is triggered manually (`workflow_dispatch`) with a branch input from the Actions tab, and on each run, it checks out the framework repo, checks out the selected branch of `polkadot-docs` into `polkadot-docs/`, sets up Python, installs `requirements.txt`, restores a Material build cache, and builds and deploys the static site.

### 2.4 Authoring and style

Content-authoring conventions are documented in the content repo's [**`CONTRIBUTING.md`](https://github.com/polkadot-developers/polkadot-docs/blob/master/CONTRIBUTING.md)**, which covers the online vs. local workflows, adding pages and sections, frontmatter fields, `.nav.yml` navigation, code snippets, images (WebP), callouts, and tutorial structure. Authoring also follows `polkadot-docs/AGENTS.md`, which points at the shared **`papermoonio/documentation-style-guide`** repo (style guide, Vale rules, vocabulary). Vale linting pulls those rules on demand rather than vendoring them.

If Parity wants the docs to be fully self-contained, the style guide and vocabulary sources are a dependency to consider migrating or forking.

### 2.5 Tested code examples (`polkadot-cookbook`)

The tutorials and code samples in the docs are backed by **`polkadot-developers/polkadot-cookbook`**, a collection of tested, runnable recipes for Polkadot SDK development. It already lives in the `polkadot-developers` org, so it is not part of the transfer, but it is part of the documentation system Parity inherits.

How it relates to the docs:

- The cookbook's `polkadot-docs/` directory mirrors the tutorial structure on [https://docs.polkadot.com/](https://docs.polkadot.com/) with test harnesses that **execute the steps a reader would follow**, so published guides stay accurate as the SDK changes. Guides link back to their corresponding harness via CI badges, giving bidirectional traceability between a tutorial and its verified code.  
- Recipes are organized across development pathways \- **pallets** (FRAME runtime logic), **contracts** (Solidity), **transactions** (Polkadot API), **XCM** (cross-chain messaging), and **networks** (Zombienet, Chopsticks). The recipe source typically lives in external repos; the cookbook holds the harnesses that clone, build, and verify them.  
- It also ships the **`dot` CLI**, a command-line tool that scaffolds new Polkadot projects (source in the `dot/` directory).

For Parity, the practical implication is that **changes to tutorial code in the docs should be kept in sync with the corresponding cookbook harness** to maintain meaningful CI verification. Maintenance of the cookbook itself follows its own repo conventions, independent of the MkDocs build.

### 2.6 Custom MkDocs plugins

The site relies on a set of custom MkDocs plugins that PaperMoon developed in the open-source **`papermoonio/mkdocs-plugins`** repo, published to PyPI as **`papermoon-mkdocs-plugins`**. They are installed as a normal Python dependency and enabled in the framework's `mkdocs.yml` `plugins:` block \- no vendored code lives in the docs or framework repos.

The plugins currently in use by the Polkadot docs include:

- **`ai_docs`** \- generates AI-ready artifacts (resolved Markdown, category bundles, site index, `llms.txt`, agent skill files) plus the per-page AI actions widget and AI resources page. Configured via `llms_config.json` (see Section 3.8).  
- **`link_processor`** \- opens external links in a new tab and normalizes trailing slashes on internal links at build time.  
- **`minify`** \- minifies HTML/CSS/JS for the built site.  
- **`page_toggle`** \- interactive toggle between variant versions of a page.  
- **`snippet_var_resolver`** \- resolves placeholder variables inside reusable snippets before rendering.  
- **`copy_md` / `instant_preview`** \- raw-Markdown serving and build-time link-preview manifests.

Because the build depends on this package, it is worth being aware of: it is open-source and installed from PyPI like any other dependency, so there is nothing to take ownership of, but it is **no longer being actively maintained** by PaperMoon. Parity may choose to pin a version, fork it, or contribute upstream. If a fully self-contained build is desired, this is one of the PaperMoon-owned dependencies to account for.

### 2.7 Planned change \- move to a monorepo

The intended direction is to **consolidate the framework and the content into a single monorepo hosted in the `polkadot-developers` org**. Instead of the current two-repo "clone content into framework at build time" arrangement, the theme/config and the Markdown content would live side by side in one repository.

Benefits of the consolidation:

- **One source of truth**: no cross-repo clone step during builds; contributors clone a single repo and run it.  
- **Simpler CI**: the build runs directly against the repo instead of stitching two repos together.  
- **Clear ownership**: everything sits under `polkadot-developers`, aligned with where the content already lives.

At a high level, the migration means moving the contents of `papermoonio/polkadot-mkdocs` (theme overrides, `mkdocs.yml`, build tooling) into a directory of the new monorepo alongside the existing `polkadot-docs` content, adjusting `docs_dir` and the build/deploy steps so they operate on the single repo, and pointing the production deploy at the new location. The MkDocs \+ Material stack itself does not change.

---

## 3\. Inside the framework repo (`polkadot-mkdocs`)

This section is the maintenance reference for the framework repo \- the parts a maintainer touches when changing the theme, build behavior, or interactive tooling. It complements (does not replace) the authoring guide in the content repo's `CONTRIBUTING.md`.

### 3.1 `mkdocs.yml` \- site configuration

The central configuration file. A few non-obvious settings:

- **`docs_dir: polkadot-docs`** \- tells MkDocs where content lives (the cloned-in content repo).  
- **`extra.glossary_tooltips.exclude_terms`** \- suppresses tooltip annotation for specific terms (currently excludes "Polkadot" to avoid over-triggering).  
- **`ENABLED_LLMS_PLUGINS`**, **`ENABLED_GIT_REVISION_DATE`**, **`SOCIAL_CARDS`** \- environment variables that gate expensive build steps; all default to `true` but can be set to `false` locally to speed up builds.

### 3.2 `hooks/`

MkDocs hooks are Python scripts that run at specific points in the build pipeline. All four are registered in `mkdocs.yml`, and each file has a docstring at the top with full usage details.

| File | What it does |
| :---- | :---- |
| `auto_index_table.py` | Replaces `<!-- INDEX TABLE START/END -->` marker blocks in index pages with auto-generated nav tables built from `.nav.yml` files |
| `footer_nav.py` | Collects pages/sections marked `footer_nav: true` in frontmatter or `.nav.yml` and passes them to the footer template |
| `glossary_abbreviations.py` | Adds `<abbr>` tooltips to glossary terms in rendered page HTML, sourced from `reference/glossary.md` in the content repo |
| `synthesize_ancestors.py` | Fixes breadcrumb rendering for orphan pages (those excluded from the nav) by reconstructing their ancestor chain from the file path |

### 3.3 `material-overrides/`

This directory is a [Material for MkDocs custom directory](https://squidfunk.github.io/mkdocs-material/customization/#extending-the-theme). Files here override or extend the upstream theme templates.

**Templates:**

| File | Purpose |
| :---- | :---- |
| `main.html` | Base template for all content pages. Adds Google Fonts, the Kapa AI chatbot widget, page keyword meta tags, custom `<title>` logic, and the announcement banner. |
| `home.html` | Template for the homepage. |
| `404.html` | Custom 404 error page. |
| `partials/` | 14 partial template overrides for nav, TOC, footer, breadcrumbs, feedback, search, and more. All have been customized \- none are 1:1 copies of the upstream Material originals. Additional partials can be overridden by copying them from the [Material for MkDocs repository](https://github.com/squidfunk/mkdocs-material) into this directory. |

**Announcement banner (recurring maintenance item).** `main.html` contains an announcement banner block:

```html
{% block announce %}
  <strong>Web3 Summit 2026</strong> | ...
{% endblock %}
```

This renders a dismissible banner at the top of every page. **Update or remove this block whenever the event it references has passed.** To hide the banner entirely, remove the `{% block announce %}` block from `main.html`.

**Kapa AI chatbot.** `main.html` loads the Kapa AI widget via a `<script>` tag. The `data-website-id` attribute identifies the Polkadot project in Kapa's system. To reconfigure the chatbot (colors, disclaimer text, etc.), all settings are data attributes on that script tag.

**Assets:**

| Path | Purpose |
| :---- | :---- |
| `material-overrides/assets/stylesheets/` | All custom CSS. `polkadot.css` is the main stylesheet; others are feature-specific (terminal blocks, timeline, toggle pages, AI file actions, etc.). |
| `material-overrides/assets/images/` | Theme images (logo, favicon, etc.). |
| `material-overrides/og-bg.webp` | Background image for social/OG cards. |

**Branding and color palette.** All color variables are defined in `polkadot.css`, structured in layers:

1. **`:root`** \- raw design tokens (greyscale, accent, semantic colors, fonts).  
2. **`[data-md-color-scheme="custom-light"]`** \- maps tokens to Material theme variables for light mode.  
3. **`[data-md-color-scheme="custom-dark"]`** \- same for dark mode.

To change a color, update the token value in `:root` rather than editing individual theme variable mappings \- the light and dark schemes pick it up automatically.

### 3.4 `layouts/`

Contains the social card layout used for Open Graph (OG) preview images. `polkadot.yml` defines the card design using Material's social plugin layout format; `og-bg.webp` (also referenced in `mkdocs.yml`) is the background image. Social card generation is controlled by the `SOCIAL_CARDS` environment variable and is disabled by default locally to speed up builds.

### 3.5 `policies/`

Contains three legal pages that are part of the site but managed separately from the content:

- `cookie-policy.md`  
- `privacy-policy.md`  
- `terms-of-use.md`

These are served at `/policies/` on the live site. Changes should go through legal review.

### 3.6 Plugin and theme asset dependencies

Several plugins and theme features require corresponding JS or CSS files to be registered in `mkdocs.yml`. If a plugin is ever removed or replaced, its assets should be removed too. All JS files live in `polkadot-docs/js/` (content repo); all CSS lives in `material-overrides/assets/stylesheets/` (framework repo).

| Asset | Type | Required by |
| ----- | :---: | ----- |
| `js/ai-file-actions.js` | JS | `ai_docs` plugin \- powers the copy/view/download dropdown on AI artifact pages |
| `assets/stylesheets/ai-file-actions.css` | CSS | `ai_docs` plugin |
| `js/toggle-pages.js` | JS | `page_toggle` plugin \- client-side toggle UI behavior |
| `assets/stylesheets/toggle-pages.css` | CSS | `page_toggle` plugin |
| `assets/stylesheets/timeline-neoteroi.css` | CSS | `neoteroi.timeline` markdown extension (customized fork of the upstream stylesheet) |
| `assets/stylesheets/terminal.css` | CSS | `termynal` terminal animation blocks used in content |
| `js/fix-created-date.js` | JS | `git-revision-date-localized` plugin \- corrects display formatting of creation dates |
| `js/header-scroll.js` | JS | Theme \- hides the header on scroll down |
| `js/search-bar-results.js` | JS | Theme \- suppresses the "Type to start searching" placeholder in the search dropdown |
| `js/root-level-sections.js` | JS | Theme \- adds a CSS class to root-level index pages for nav styling |
| `js/error-modal.js` | JS | Theme \- reusable error modal used by other interactive scripts |
| `js/connect-to-metamask.js` | JS | Loaded globally (not per-page) \- only activates on pages that contain `.connect-metamask` elements |

### 3.7 Interactive tools

Several pages embed browser-side interactive widgets. These are self-contained \- they run entirely client-side using Polkadot.js libraries loaded from a CDN.

**Important:** the JavaScript lives in `polkadot-docs/js/` (content repo); the CSS lives in `material-overrides/assets/stylesheets/` (framework repo). Changes to behavior go in `polkadot-docs`; changes to visual styling go here. Pages load their widgets by adding `extra_javascript` and `extra_css` entries to their frontmatter, then rendering each widget into a named `<div id="...">` element in the page body.

**Polkadot Utilities (`tools/index.md`).** A single page hosting several utility widgets, all loaded together via frontmatter. The Polkadot.js libraries (`@polkadot/util`, `@polkadot/util-crypto`, `@polkadot/keyring`) are loaded from a pinned CDN version \- update the version numbers in the frontmatter if the libraries need upgrading.

| Widget | Div ID | JS file | CSS file |
| :---- | :---- | :---- | :---- |
| Encoding & Decoding | `encoding-root` | `polkadot-utilities.js` | `polkadot-utilities.css` |
| Hashing | `hashing-root` | `polkadot-utilities.js` | `polkadot-utilities.css` |
| Address Utilities | `address-root` | `polkadot-utilities.js` | `polkadot-utilities.css` |
| EVM ↔ SS58 Address Converter | `account-converter-root` | `account-converter.js` | `account-converter.css` |
| Asset ID → ERC20 Address | `erc20-converter-root` | `erc20-asset-converter.js` | `erc20-asset-converter.css` |

The account converter and ERC20 converter also appear individually on other pages (e.g., `smart-contracts/for-eth-devs/accounts.md`, `smart-contracts/precompiles/erc20.md`) using the same pattern.

**Connect to MetaMask (`smart-contracts/connect.md`).** Buttons on this page trigger MetaMask network-add prompts for Polkadot Hub (mainnet and testnet), powered by `connect-to-metamask.js`. The network configurations (chain IDs, RPC URLs, block explorer URLs) are hardcoded in that file; update them there if the network details change.

### 3.8 `llms_config.json`

Configures the `ai_docs` plugin, which generates machine-readable content artifacts for LLM consumption. Key fields:

- `project` \- site identity and MCP server URL (`docs-mcp.polkadot.com`).  
- `repository` \- points to the `polkadot-docs` GitHub repo (used to resolve source links).  
- `content.categories_info` \- defines the content taxonomy used to group AI artifacts.  
- `content.exclusions.skip_basenames` \- files to exclude from AI artifact generation (legal pages, etc.).  
- `outputs.public_root` \- where artifacts are published (`/ai/`).

The AI artifacts directory (`/ai/`) is blocked from search engine indexing in `robots.txt` to prevent duplicate content issues.

### 3.9 `redirects.json` and `update_redirects.py`

[`redirects.json`](https://github.com/papermoonio/polkadot-mkdocs/blob/main/redirects.json) is the single source of truth for the site's redirects \- a list of URL redirects in `{ "key": "/old/path/", "value": "/new/path/" }` format.

**When to update:** any time a page in `polkadot-docs` is renamed or deleted, add a redirect so existing links and search results don't break.

`scripts/update_redirects.py` **must be run manually any time a page in `polkadot-docs` is renamed, moved, or deleted.** It inspects a GitHub PR for those changes and updates `redirects.json` accordingly (see the comment block at the top of the script for usage). After running, search `redirects.json` for `TODO: UPDATE_ME` and replace any placeholders with the appropriate destination URLs before merging.

**Server-side vs. client-side redirects (recommendation for Parity).** PaperMoon serves these as **server-side redirects**, driven from `redirects.json`. In the current setup, this required some Cloudflare-specific configuration to work, so the exact mechanism is environment-specific and not included with the repo. MkDocs *can* also produce **client-side redirects** (meta-refresh/JS redirect pages generated at build time), which is the simpler option and works on any static host with no CDN configuration.

**We strongly recommend implementing server-side redirects** rather than client-side ones: they return proper HTTP 3xx responses, which is better for SEO (link equity is preserved and search engines follow them cleanly) and provide a faster redirect for users. Whichever approach Parity chooses, `redirects.json` remains the source of truth for the redirect list \- only the delivery mechanism differs.

### 3.10 `requirements.txt`

Python package dependencies for the MkDocs build, pinned to specific versions for reproducibility.

**Important:** treat MkDocs and Material for MkDocs as frozen dependencies \- upgrade only if strictly necessary and test thoroughly, as updates may introduce breaking changes.

**When to update:** when adding a new plugin or resolving a dependency conflict. After updating, run `make reinstall` locally and verify `make build` passes before committing.

### 3.11 Recurring maintenance items (summary)

The items most likely to need ongoing attention after handover:

- **Announcement banner** (Section 3.3) \- update or remove when the referenced event passes.  
- **Redirects** (Section 3.9) \- run `update_redirects.py` whenever pages are renamed/moved/deleted, and resolve `TODO: UPDATE_ME` placeholders.  
- **Frozen build dependencies** (Section 3.10) \- MkDocs/Material pinned; upgrade cautiously.  
- **Unmaintained plugin package** (Section 2.6) \- `papermoon-mkdocs-plugins` is open-source but no longer actively maintained; decide whether to pin, fork, or contribute upstream.  
- **Pinned CDN libraries** (Section 3.7) \- Polkadot.js versions in interactive-tool frontmatter; update when upgrading.  
- **MetaMask network configs** (Section 3.7) \- hardcoded in `connect-to-metamask.js`.

---

## 4\. MCP server

The MCP server exposes the documentation to AI clients (Claude, Cursor, VS Code, etc.) over the Model Context Protocol, providing search and document retrieval tools for the docs content. This section is **guidance**, not a transfer: the server is an open-source tool Parity can use as-is or self-host, and the docs build/hosting handover does not depend on it.

### 4.1 The server

`papermoon-mkdocs-mcp` is a **generic, open-source MCP server for any MkDocs project**, published to PyPI. It is not Polkadot-specific \- it reads Markdown directly from a MkDocs project on disk and serves it. Parity can install it from PyPI and point it at the Polkadot docs; there is nothing to fork or take ownership of.

Key characteristics:

- **Tools exposed:** `search`, `read_document`, `list_documents`, `get_project_info`, `get_document_outline`.  
- **Search:** SQLite FTS5 keyword search (BM25) out of the box, with optional semantic/vector search and a hybrid mode.  
- **Indexing:** builds a persistent SQLite index at startup and updates it incrementally as files change.  
- **Transports:** `stdio` for local clients, or `streamable-http` / `sse` for networked/multi-client setups.

Running it locally against a checkout is as simple as:

```shell
cd /path/to/mkdocs-project
papermoon-mkdocs-mcp --config /path/to/mkdocs.yml
```

For a hosted deployment, it is run with the HTTP transport (`--transport streamable-http`) behind a TLS-terminating reverse proxy.

### 4.2 Running a hosted server

The server itself is portable \- a standard pip-installable MCP server, so it can be hosted on whatever infrastructure Parity prefers. The reference deployment that currently serves [https://mkdocs-mcp.papermoon.io/polkadot/mcp](https://mkdocs-mcp.papermoon.io/polkadot/mcp) runs it as a **stateless AWS ECS Fargate service** behind an Application Load Balancer, using the Streamable HTTP transport. The pattern below describes that setup so it can be reproduced or adapted.

**Container shape.** A single MCP deployment is one task made up of three cooperating containers:

1. **sync** \- clones the framework \+ content repos and periodically re-fetches them, signaling when the docs have changed.  
2. **mcp-server** \- the `papermoon-mkdocs-mcp` server; waits for the docs to be present, serves MCP requests over HTTP, and restarts when the sync container reports an update.  
3. **router** \- an nginx reverse proxy that strips the URL path prefix (so a load balancer can route `/polkadot/mcp` to the server's `/mcp`) and optionally serves a custom host.

This is what keeps the server current without a rebuild: the **sync** container pulls the latest content at intervals, and the **mcp-server** reindexes.

**Infrastructure.** The reference deployment defines its AWS resources as infrastructure-as-code, split into three concerns worth reproducing on any platform:

- **Shared base infrastructure** \- networking (VPC \+ public subnets), the load balancer, the ECS cluster, and a **monthly budget cap** that stops the services if spend exceeds a configured threshold.  
- **Per-site service** \- one service per documentation site (e.g., Polkadot), parameterized with the framework repo URL, the content repo URL, the URL path prefix, task CPU/memory, the docs-update check interval, and an optional custom hostname.  
- **Routing** \- an optional host-header rule (and TLS certificate) for serving a deployment on its own subdomain.

**Security note:** because the HTTP transport binds to a non-loopback address, the server must sit behind a TLS-terminating reverse proxy/load balancer (as the `router` \+ ALB do here). Do not expose it directly.

### 4.3 Operating it

Common operational tasks for the reference (AWS ECS) deployment:

- **Logs & metrics:** CloudWatch log groups (one each for the router, server, and sync containers) and the ECS console.  
- **Updating the server:** the MCP image installs the latest `papermoon-mkdocs-mcp` from PyPI; to ship a change, rebuild the image, push it to the container registry, and force a new service deployment.  
- **Deploying a new site:** stand up a new per-site service stack pointing at the relevant framework \+ content repos.  
- **Budget trip:** if the budget cap fires, set every service's desired task count to `0`; after investigating the cause, reset the desired task count to `1`.  
- **Decommissioning:** tear down the relevant infrastructure stack(s).

---

## 5\. Handover checklist

To take over the operation, Parity will need:

- [ ] **Repo ownership/access** \- transfer or grant access to `papermoonio/polkadot-mkdocs`. (`polkadot-developers/polkadot-docs` already sits in the target org. The MCP server is a separate open-source tool and is not part of the transfer.)  
- [ ] **Hosting/infrastructure** \- provision the infrastructure that will run the docs build/deploy and the MCP server under Parity/Polkadot control.  
- [ ] **Publishing pipeline** \- implement a build-and-serve pipeline for production (Section 2.3); the internal PaperMoon process is not transferred, so Parity provides its own.  
- [ ] **DNS/domains** \- control of `docs.polkadot.com` and a domain for the MCP endpoint under Parity/Polkadot control.  
- [ ] **Style-guide dependency** \- decide whether to keep depending on `papermoonio/documentation-style-guide` for authoring/Vale, or fork it under a Polkadot-owned org.  
- [ ] **Plugin dependency** \- decide whether to keep depending on `papermoon-mkdocs-plugins` (open-source, no longer actively maintained), pin a version, or fork it.  
- [ ] **Monorepo migration** \- agree on the target repo in `polkadot-developers` and execute the framework \+ content consolidation described in Section 2.7.

---

## 6\. Open items/decisions for Parity

- **Publishing pipeline**: production is published via an internal PaperMoon process that is not part of the transfer (Section 2.3). Parity implements its own build-and-serve pipeline; any approach that runs the MkDocs build and hosts the static output at the target domain works, and `deploy-docs.yml` can serve as a starting reference.  
- **MCP endpoint hosting**: the current endpoint lives under a PaperMoon domain. If Parity wants the MCP server under its own control, it can self-host the open-source server using the pattern in Section 4.2 and point it at a Polkadot/Parity-owned domain. The server is portable, so the hosting choice is open.  
- **Monorepo timing:** whether to migrate to the monorepo before or after the docs handover. Doing it first means Parity inherits a simpler, single-repo build.


# Agent Tasks Config Generator — Skill File

## Purpose

This skill guides an AI agent through the process of analyzing a documentation project and its associated reference repositories to produce an `agent_tasks_config.json` file. That config is then consumed by the `agent_tasks` build plugin to generate self-contained, agent-optimized task files at build time.

This skill is used both for **initial setup** (creating the first config for a project) and **ongoing maintenance** (adding new tasks or updating existing ones as documentation evolves). The output is a committed config file that the build pipeline uses on every subsequent build. The agent running this skill is *not* the same agent that will later consume the task files — this agent is a collaborator helping a documentation engineer set up and maintain the config.

---

## Context: LLM Ready vs Agent Ready

Documentation projects using the `resolve_md` plugin already produce **LLM Ready** artifacts — clean, resolved markdown pages optimized for context-window use cases where an LLM answers questions for a user.

**Agent Ready** is a separate tier. Agents completing tasks independently need different things than LLMs answering questions:

| LLM Ready | Agent Ready |
|---|---|
| Clean prose explaining concepts | Sequential steps with concrete commands |
| Resolved snippets inline | Fetchable URLs to complete, working code files |
| Category bundles for broad context | Single task files scoped to one workflow |
| Optimized for comprehension | Optimized for execution |

The `agent_tasks_config.json` bridges the gap by defining task workflows that the build plugin assembles into agent-consumable files.

---

## What You Will Produce

A new or updated `agent_tasks_config.json` file. This file lives in the project root alongside `llms_config.json`.

Below is an annotated skeleton showing the shape of the config with one task containing three representative steps — a command step, a reference file step, and a step with expected output. Every task you produce should follow this structure.

```json
{
    "schema_version": "0.1",

    "project": {
        "id": "<from llms_config.json>",
        "name": "<from llms_config.json>",
        "docs_base_url": "<from llms_config.json>"
    },

    "reference_repos": {
        "<repo-id>": {
            "url": "https://github.com/<org>/<repo>",
            "default_branch": "main",
            "raw_base_url": "https://raw.githubusercontent.com/<org>/<repo>/main",
            "description": "<what this repo provides>"
        }
    },

    "tasks": [
        {
            "id": "verb-noun-qualifier",
            "title": "Human-Readable Task Title",
            "objective": "One sentence: what the agent will have accomplished by the end.",

            "prerequisites": {
                "runtime": ["Node.js v22+", "npm"],
                "network": ["RPC endpoint: <url>"],
                "tokens": ["Testnet tokens from <faucet-url>"]
            },

            "env_vars": [
                {
                    "name": "EXAMPLE_KEY",
                    "description": "What this is and where to get it.",
                    "required": true
                }
            ],

            "steps": [
                {
                    "order": 1,
                    "action": "Initialize the project",
                    "commands": ["mkdir my-project", "cd my-project", "npm init -y"],
                    "description": "Setup step using commands only — no reference file needed."
                },
                {
                    "order": 2,
                    "action": "Create the config file",
                    "reference_file": "src/config.ts",
                    "description": "Fetch the reference file and save it as src/config.ts. In the fetched file, replace 'http://localhost:8080' with '<production-rpc-url>'."
                },
                {
                    "order": 3,
                    "action": "Build and verify",
                    "commands": ["npm run build"],
                    "expected_output": "Build completed successfully with no errors."
                }
            ],

            "reference_code": {
                "repo": "<repo-id>",
                "base_path": "examples/my-task",
                "files": [
                    {
                        "path": "src/config.ts",
                        "description": "One-line summary of what this file does"
                    }
                ]
            },

            "error_patterns": [
                {
                    "pattern": "Error: Cannot find module 'example'",
                    "cause": "Dependency not installed.",
                    "resolution": "Run npm install example."
                }
            ],

            "supplementary_context": {
                "description": "When to consult these pages — for understanding why, not how.",
                "pages": [
                    {
                        "slug": "page-slug",
                        "url": "<docs_base_url>/ai/pages/page-slug.md",
                        "relevance": "Why an agent might need this page"
                    }
                ]
            }
        }
    ],

    "outputs": {
        "public_root": "/ai/",
        "tasks_dir": "tasks"
    }
}
```

If an `agent_tasks_config.json` already exists in the project, read it before starting — you may be adding a task to an existing config rather than creating one from scratch. See Phase 4 for merge behavior.

**For a real-world example** of a completed config with a multi-step task, read the `agent_tasks_config.json` in this project's root directory.

---

## Before You Begin

### Step 1: Verify the Documentation Project

Confirm you are inside a valid documentation project by checking for:

- `mkdocs.yml` in the project root
- `llms_config.json` in the project root (the `resolve_md` plugin must already be configured)

If either is missing, stop and inform the documentation engineer — this skill requires an existing MkDocs project with `resolve_md` set up.

Read `llms_config.json` to capture:
- Project identity (`project.id`, `project.name`, `docs_base_url`)
- Content categories (`content.categories_info`) — these tell you the domain areas the docs cover
- Output paths (`outputs`) — where resolved pages will be served from

### Step 2: Discovery Interview

The documentation engineer is your human collaborator. Before diving into analysis, conduct a brief interview to understand the scope of work. Ask the following questions (you can present them all at once):

1. **What task(s) do you want to build?** Do you have specific tasks identified, or would you like help surfacing task candidates from the docs?
2. **Do you have a reference repository** (or repositories) containing working, tested code for the task(s)? If so, provide the URL(s).
3. **What are the common pitfalls?** When someone follows this workflow manually, what typically goes wrong? (This feeds error patterns later.)

Based on the answers, determine your path through the remaining phases:

| Answer | Effect |
|---|---|
| Engineer has specific tasks | Skip the doc-scanning steps in Phase 1 (steps 1-3) and proceed directly to Phase 2 with the tasks they provide |
| Engineer wants help finding tasks | Complete all of Phase 1 to scan docs and propose candidates |
| Engineer provides reference repo(s) | Use them in Phase 2; still scan the docs for any additional repos the engineer may have missed |
| Engineer has no reference repo | Scan the docs for repo links in Phase 2; if none are found, flag this to the engineer — tasks without reference code are possible but significantly weaker |

---

## Process

### Phase 1: Identify Task Candidates

**Goal:** Scan the docs and propose tasks to build. Skip steps 1-3 if the engineer provided specific tasks in the discovery interview.

1. Scan the docs directory structure:
   - Read `.nav.yml` files to understand the navigation hierarchy and logical groupings
   - Identify tutorial/guide pages vs reference pages vs conceptual pages
   - Note which pages walk users through multi-step workflows — these are your task candidates

2. Read frontmatter on candidate pages:
   - `title` and `description` for understanding scope
   - `categories` for understanding which domain areas a page covers

3. Identify task-shaped content:
   - Pages or page sequences that walk through a complete workflow from start to finish
   - Content that has a clear objective (e.g., "by the end of this guide, you will have...")
   - Multi-page flows connected by navigation ordering

**Output of this phase:** A list of candidate tasks with:
- A working title for each task
- A proposed task ID following the naming convention: `verb-noun-qualifier`, lowercase, hyphen-separated (e.g., `build-zero-to-hero-dapp`, `deploy-erc20-contract`, `setup-validator-node`). The ID must be URL-safe and descriptive enough to distinguish from other tasks at a glance
- The doc pages involved
- The approximate scope (what does the user accomplish?)

**Checkpoint:** Present the candidate task list to the documentation engineer for validation before proceeding.

---

### Phase 2: Analyze the Reference Repository

**Goal:** Map working reference code to the candidate tasks. Use the reference repo(s) provided in the discovery interview. If none were provided, start at step 3 to scan the docs for repo links.

1. **Examine the provided reference repo structure:**
   - Clone or browse the repo to understand its directory layout
   - Identify the main code files and their purposes
   - Note the language, runtime, and dependency requirements
   - **Check the repo's own dependency versions** — read `package.json`, `Cargo.toml`, `requirements.txt`, or equivalent to determine which tool versions the reference code was written for. Record these versions; you will need them in Phase 3 to ensure the task steps specify compatible versions.

2. **Scan the docs for additional reference repos:** Look through the candidate task pages for:
   - GitHub repository links (clone URLs, badge links, "View source" links)
   - Code snippet includes that reference external repos (e.g., `--8<--` paths, submodule references)
   - "Where to Go Next" or conclusion sections that link to working example repos
   - Present any additional repos found to the engineer for confirmation before including them

3. For each confirmed reference repo, construct the entry:
   - `url`: The GitHub URL of the repo
   - `default_branch`: The branch to reference (usually `main`)
   - `raw_base_url`: Constructed as `https://raw.githubusercontent.com/{org}/{repo}/{branch}`
   - `description`: What this repo provides

4. For each candidate task, identify:
   - Which files from the reference repo(s) are needed
   - The logical order in which an agent should create/use those files
   - The base path within the repo (e.g., `node/scripts`, `examples/python`)

5. For each file, determine:
   - `path`: Relative path from the base path
   - `description`: One-line summary of what this file does

6. **Version compatibility audit** — compare the tool versions used in the reference code against the versions you plan to specify in the task steps. Look for:
   - **Major version mismatches** — e.g., reference code written for v2 of a framework but the task will specify v3. Check changelogs or migration guides for breaking changes in config format, plugin registration, module system (`"type": "module"` requirements), and API patterns.
   - **Dependency manifest completeness** — read the reference repo's lockfile or dependency manifest to capture the full dependency tree, including peer dependencies that won't auto-install. Note any transitive dependencies that require manual installation.
   - **Hardcoded values that differ from task context** — scan reference files for values like localhost URLs, placeholder chain IDs, default ports, or example API keys that will need to be replaced with task-specific values. Record each one as a substitution pair (reference value → task value).

   If you find version mismatches, **ask the documentation engineer:** "The reference code uses [tool vX] but the docs recommend [tool vY]. Should the task target the reference code's version, or should I note the required adaptations for vY?" Do not silently specify a different version than the reference code was built against.

**Output of this phase:** A complete `reference_repos` block, a `reference_code` block for each task, a list of any version mismatches or required adaptations, and a substitution map of hardcoded values that differ from the task context.

---

### Phase 3: Define Task Steps

**Goal:** Create the sequential execution plan for each task.

For each candidate task:

1. **Write the objective** — one sentence describing what the agent will accomplish. Be specific and outcome-oriented.

2. **Define prerequisites** — group by type:
   - `runtime`: Language versions, package managers, build tools
   - `network`: Network access, API endpoints, chain connections
   - `tokens`: Testnet tokens, API keys, credentials needed
   - Add other groups as needed for the project

3. **Define environment variables** — for each:
   - `name`: The variable name exactly as it appears in code
   - `description`: What it is and where to get it
   - `required`: Whether the task cannot proceed without it

4. **Define steps** — each step should have:
   - `order`: Sequential number
   - `action`: Short imperative description of what to do
   - `description` (optional): More detail if the action isn't self-explanatory
   - `commands` (optional): Literal shell commands to run — use these for setup steps like project init, dependency installation, and execution
   - `reference_file` (optional): Points to a file in `reference_code` — use these for steps where the agent needs to create or understand a code file
   - `expected_output` (optional): What success looks like — use for the final execution step or key milestones

   **Guideline:** A step should either have `commands` (do this) or `reference_file` (create/use this code), rarely both. Keep steps atomic — one action per step.

   **Writing descriptions for agent clarity:** The consuming agent has no prior context — descriptions must be unambiguous and explicit. Apply these rules:

   - **Interactive commands:** If a command prompts for user input (e.g., `npx hardhat --init`, deployment confirmations), the description must flag it as interactive **and provide a non-interactive fallback**. Agents typically run in non-interactive shells where prompts will fail. For each interactive command, include one of:
     - A CLI flag or piped input that bypasses the prompt (e.g., `--yes`, `echo "y" | ...`)
     - A complete manual scaffold alternative — list every file, directory, and dependency the interactive command would have created, so the agent can reproduce the result without running the interactive command
     - If no non-interactive alternative exists, mark the step with `"interactive": true` in the description and state that the agent must delegate this step to the user
   - **File operations — be explicit about the verb:** Don't say "update" or "adapt" a file when you mean "replace entirely." Use precise language:
     - "Fetch the reference file and save it as `<path>`" — for new files
     - "Replace the generated `<filename>` entirely with the fetched reference file" — when a previous step created a file that should be overwritten
     - "Delete any default files in `<directory>`, then fetch and save the reference file as `<path>`" — when scaffold tools generate placeholder files
   - **Cross-step data dependencies:** If a step produces a value that a later step needs (e.g., a deployed contract address, a generated API key, a build artifact path), the producing step's description must say "save this value — you will need it in step N" and the consuming step's description must say exactly what to substitute and where. Never assume the agent will infer that a hardcoded value in a reference file should be replaced.
   - **File placement:** When a reference file path could be ambiguous (e.g., the repo structure differs from what the tutorial text describes), the description should state the exact destination path relative to the current working directory and note where other files expect to import it from.
   - **Reference file substitutions:** If Phase 2 identified hardcoded values in a reference file that differ from the task context (e.g., a localhost URL that should be a production RPC endpoint, a default chain ID that should be a testnet chain ID), the step description must list each substitution explicitly: "In the fetched file, replace `<old value>` with `<new value>`." Do not use vague instructions like "adapt to your environment" — the agent has no way to infer which values to change.
   - **Secrets and private keys — always use the `.env` file pattern:** Agents run inside tools like Claude Code where the user's shell environment is not shared and interactive secret prompts create security and usability problems. For any task that requires secrets (private keys, API keys, tokens):
     1. **Always use dotenv:** Include `dotenv` in the dependency install step. For ESM projects, add `import "dotenv/config";` as the first line of the config file. For CommonJS projects, add `require("dotenv").config();` as the first line.
     2. **Create a `.env` + `.gitignore` step:** Add a dedicated step that creates a `.env` file with empty placeholder values (e.g., `PRIVATE_KEY=`) and a `.gitignore` that excludes `.env`. This step's description must include this exact instruction: *"IMPORTANT: After creating these files, stop and ask the user to edit the .env file and paste their secret value. Do NOT ask the user to type or paste secrets in the chat — they should edit the .env file directly in their editor or file system. Wait for the user to confirm before proceeding."*
     3. **Never use shell exports or interactive prompts for secrets:** Do not instruct the agent to run `export SECRET=...` (the agent's shell is ephemeral and not shared with the user's terminal) or interactive commands like `npx hardhat vars set` (the agent would need to ask for the secret, which sends it through the chat). If the reference code uses a tool-specific secret mechanism (e.g., Hardhat config variables, encrypted keystores), add substitution instructions to convert it to dotenv.
     4. **Gate deployment/test steps on the secret:** Any step that requires the secret must include: *"Before running this command, confirm the user has added their key to the .env file (step N)."*

4a. **Define the dependency manifest** — for steps that install packages, list the complete install command including:
   - All top-level packages with version constraints
   - Peer dependencies that won't auto-install (check the reference repo's lockfile)
   - Module system requirements (e.g., `"type": "module"` in `package.json` for ESM-only tools)
   - Any post-install configuration commands (e.g., `npm pkg set type="module"`)

   **Why this matters:** Many tools have peer dependencies, plugin registrations, or module system requirements that aren't obvious from the top-level install command. If the agent hits a missing peer dependency error mid-workflow, it has to guess which packages to add. Listing everything upfront makes installation deterministic.

5. **Define error patterns** — for each known failure mode:
   - `pattern`: The error message or symptom the agent might encounter
   - `cause`: Why this happens
   - `resolution`: How to fix it

   **Sources for error patterns:** The docs' troubleshooting pages, the reference repo's issues, and the documentation engineer's experience. Ask the engineer explicitly: "What are the most common things that go wrong when someone follows this workflow?"

6. **Define supplementary context** — identify resolved doc pages that provide deeper explanation:
   - `slug`: The page slug matching the resolve_md output filename
   - `url`: The full URL to the resolved page (constructed from `docs_base_url` + `outputs.public_root` + `outputs.files.pages_dir` + `/{slug}.md` in `llms_config.json`)
   - `relevance`: Why an agent might need this page

   **Guideline:** These are fallback resources. The agent's primary path is the steps + reference code. Supplementary context is for when the agent needs to understand *why* something works, not *how* to do it.

**Checkpoint:** Present the complete task definition to the documentation engineer for review before finalizing.

---

### Phase 4: Assemble the Config

**Goal:** Produce the final `agent_tasks_config.json`.

**Before assembling, check if `agent_tasks_config.json` already exists in the project root.**

- **If it exists:**
   1. Read it and use it as the base config.
   2. Preserve existing `project`, `reference_repos`, and `outputs` blocks — only update them if the values in `llms_config.json` have changed.
   3. Scan the existing `tasks` array for tasks with the same or similar `id` or `title` as the new task being created. If a match is found, **ask the documentation engineer:** "A task with a similar name already exists: `<existing task title>` (`<existing task id>`). Would you like to update the existing task or create a new, separate task?" Do not silently overwrite or duplicate.
   4. If updating an existing task, replace that task entry in the array. If creating a new task, append it. In either case, merge any new `reference_repos` entries without removing existing ones.

- **If it does not exist:** Start from an empty config structure and proceed with the steps below.

1. **Set the project block** — mirror the relevant fields from `llms_config.json`:
   ```json
   "project": {
       "id": "<from llms_config>",
       "name": "<from llms_config>",
       "docs_base_url": "<from llms_config>"
   }
   ```

2. **Set the reference_repos block** — one entry per reference repository:
   ```json
   "reference_repos": {
       "<repo-id>": {
           "url": "https://github.com/<org>/<repo>",
           "default_branch": "main",
           "raw_base_url": "https://raw.githubusercontent.com/<org>/<repo>/main",
           "description": "<what this repo provides>"
       }
   }
   ```

3. **Set the tasks array** — one entry per task, using all the data from Phases 1-3.

4. **Set the outputs block**:
   ```json
   "outputs": {
       "public_root": "/ai/",
       "tasks_dir": "tasks"
   }
   ```
   The `public_root` should match the value in `llms_config.json`. The `tasks_dir` is the subdirectory within the AI output where task files will be written.

5. **Set the schema_version** to `"0.1"`.

---

### Phase 5: Validate

Before delivering the config:

1. **Structural check** — verify the JSON is valid and all required fields are present
2. **Reference check** — verify that every `reference_file` in a step has a corresponding entry in the task's `reference_code.files` array, and that every entry in `reference_code.files` is actually referenced by at least one step (remove unused entries)
3. **URL check** — verify that `raw_base_url` + `base_path` + `path` constructs a valid GitHub raw URL for each reference file
4. **Supplementary page check** — verify that referenced page slugs correspond to actual pages in the docs
5. **Step ordering check** — verify steps are sequential and logically ordered (setup before implementation, implementation before execution)
6. **Completeness check** — could an agent with no prior knowledge of this project follow the steps from start to finish using only the task file and fetchable reference code?
7. **Version compatibility check** — for each task, verify:
   - The tool versions specified in step commands (e.g., `hardhat@3.0.9`) are compatible with the reference code's patterns (config format, plugin API, import style). If the reference code was written for a different major version, either adjust the version in the steps to match, or document every required adaptation in the step descriptions.
   - Pinned versions don't conflict with plugin/dependency version requirements. Check that the pinned version falls within the `peerDependencies` range of every plugin the task installs.
   - The dependency install steps include all peer dependencies and module system requirements — not just the top-level packages.
8. **Substitution completeness check** — for each reference_file step, verify:
   - Every hardcoded value in the reference file that differs from the task context has an explicit substitution instruction in the step description. Scan reference files for URLs, chain IDs, port numbers, addresses, and API keys that are context-specific.
   - No step description uses vague adaptation language ("adapt to your environment", "update as needed", "configure appropriately"). Every change the agent must make should be stated as a concrete find-and-replace.
9. **Agent clarity check** — walk through each step as if you are an agent seeing it for the first time and verify:
   - **Interactive commands have non-interactive fallbacks:** Does any `commands` entry invoke a tool that prompts for input (e.g., `init` commands, deployment confirmations, interactive menus)? If so, the `description` must provide a non-interactive alternative (CLI flags, piped input, or a manual scaffold file list). Simply describing the prompt is not sufficient — agents in non-interactive shells need a way to bypass it entirely.
   - **File operations are unambiguous:** Does every reference_file step make it clear whether the agent should create a new file, replace an existing generated file, or merge into an existing file? Vague verbs like "update" or "adapt" will cause agents to hesitate or guess wrong.
   - **Cross-step data flows are explicit:** If step N produces a value (contract address, artifact path, generated key) that step M consumes, do both steps mention the dependency by step number? Check reference files for hardcoded values that the agent must substitute — these are easy to miss.
   - **File paths resolve correctly:** For each reference_file step, does the destination path match what other files in the project import? Check import statements in the reference code to confirm paths are consistent.

---

## Schema Reference

### Top Level

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Schema version, currently `"0.1"` |
| `project` | object | yes | Project identity |
| `reference_repos` | object | yes | Map of repository ID to repo metadata |
| `tasks` | array | yes | Array of task definitions |
| `outputs` | object | yes | Output path configuration |

### project

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Project identifier (match `llms_config.json`) |
| `name` | string | yes | Human-readable project name |
| `docs_base_url` | string | yes | Base URL of the published docs site |

### reference_repos[id]

| Field | Type | Required | Description |
|---|---|---|---|
| `url` | string | yes | GitHub repository URL |
| `default_branch` | string | yes | Branch to reference for raw URLs |
| `raw_base_url` | string | yes | Base URL for raw file access |
| `description` | string | yes | What this repo provides |

### tasks[]

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | URL-safe task identifier using `verb-noun-qualifier` convention (e.g., `build-zero-to-hero-dapp`) |
| `title` | string | yes | Human-readable task title |
| `objective` | string | yes | One sentence describing what the agent accomplishes |
| `prerequisites` | object | yes | Grouped prerequisite lists |
| `env_vars` | array | yes | Environment variables needed (can be empty array) |
| `steps` | array | yes | Sequential execution steps |
| `reference_code` | object | yes | Index of fetchable code files |
| `error_patterns` | array | yes | Known failure modes and fixes (can be empty array) |
| `supplementary_context` | object | yes | Links to resolved doc pages for deeper context |

### tasks[].steps[]

| Field | Type | Required | Description |
|---|---|---|---|
| `order` | integer | yes | Sequential step number |
| `action` | string | yes | Short imperative description |
| `description` | string | no | Additional detail |
| `commands` | array | no | Literal shell commands |
| `reference_file` | string | no | Path to file in `reference_code` |
| `expected_output` | string | no | What success looks like |

### tasks[].reference_code

| Field | Type | Required | Description |
|---|---|---|---|
| `repo` | string | yes | Key into `reference_repos` |
| `base_path` | string | yes | Directory within the repo containing the files |
| `files` | array | yes | Array of file entries |

### tasks[].reference_code.files[]

| Field | Type | Required | Description |
|---|---|---|---|
| `path` | string | yes | File path relative to `base_path` |
| `description` | string | yes | One-line summary of the file's purpose |

### tasks[].env_vars[]

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Variable name as used in code |
| `description` | string | yes | What it is and where to get it |
| `required` | boolean | yes | Whether the task fails without it |

### tasks[].error_patterns[]

| Field | Type | Required | Description |
|---|---|---|---|
| `pattern` | string | yes | Error message or symptom |
| `cause` | string | yes | Why this happens |
| `resolution` | string | yes | How to fix it |

### tasks[].supplementary_context

| Field | Type | Required | Description |
|---|---|---|---|
| `description` | string | yes | Guidance for the consuming agent on when to use these |
| `pages` | array | yes | Array of page references |

### tasks[].supplementary_context.pages[]

| Field | Type | Required | Description |
|---|---|---|---|
| `slug` | string | yes | Page slug matching resolve_md output |
| `url` | string | yes | Full URL to the resolved page |
| `relevance` | string | yes | Why an agent might need this page |

### outputs

| Field | Type | Required | Description |
|---|---|---|---|
| `public_root` | string | yes | Root path for AI artifacts (match `llms_config.json`) |
| `tasks_dir` | string | yes | Subdirectory for task file output |

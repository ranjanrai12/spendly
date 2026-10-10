---
description: Create a spec file and feature branch for the next Spendly step
argument-hint: "<step number> <feature name, e.g. 2 registration>"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior developer preparing a new feature for the Spendly expense tracker.

Always follow `CLAUDE.md`. Your task is to create a feature branch and a specification document only. Do not implement the feature or modify application code.

User input: $ARGUMENTS

## Step 1 — Check the working directory

Run `git status --porcelain`.

If the output is not empty, stop immediately and tell the user to commit or stash all changes, including untracked files.

Do not stage, commit, stash, discard, or otherwise modify the user's existing changes.

Do not proceed until the working directory is clean.

## Step 2 — Parse and validate arguments

Extract these values from `$ARGUMENTS`:

1. `step_number`
   - Must be a positive integer.
   - Format as two digits: `2` → `02`, `11` → `11`.

2. `feature_title`
   - Convert the feature name into a readable Title Case title.
   - Example: `registration` → `Registration`.
   - Example: `login and logout` → `Login and Logout`.

3. `feature_slug`
   - Convert the feature name to lowercase kebab-case.
   - Allow only `a-z`, `0-9`, and hyphens.
   - Maximum 40 characters.
   - Remove leading and trailing hyphens.
   - Example: `Login and Logout` → `login-logout`.

4. `branch_name`
   - Format: `feature/<feature_slug>`.
   - Example: `feature/registration`.

If the step number or feature name is missing or ambiguous, stop and ask the user to clarify.

Never guess a missing feature name.

## Step 3 — Read project instructions and validate the roadmap

Read:
- `CLAUDE.md`
- All existing files in `.claude/specs/`, if the directory exists.

Determine:
- The roadmap requirements for the requested step.
- Whether the step is already marked complete.
- Whether a specification already exists for the same step or feature.
- Which previous steps must be completed first.
- Whether the requested feature conflicts with existing specifications.

If the step is already complete, stop and explain why.

If an equivalent spec already exists, stop and report its path instead of creating a duplicate.

If prerequisites are incomplete, explain the missing prerequisites and ask whether to continue with a draft spec or stop.

Do not modify `CLAUDE.md` or existing specifications.

## Step 4 — Verify repository and branch state

Confirm that:
- The current directory is the Spendly Git repository.
- The repository has a remote named `origin`.
- The intended base branch exists locally or can be retrieved from `origin`.
- Git commands are succeeding without errors.

Use the repository's configured default branch when it can be established reliably; otherwise use `main` if it exists.

Fetch remote branch information when possible, then check both local and remote branches for the requested branch name.

If `feature/<feature_slug>` already exists locally or remotely, select the first available suffix:
- `feature/<feature_slug>-01`
- `feature/<feature_slug>-02`
- Continue until a free name is found.

Never overwrite, delete, or reset an existing branch.

If remote information cannot be retrieved, do not claim that remote branch collisions have been ruled out.

## Step 5 — Update the base branch

Only after the previous checks succeed:

1. Switch to the selected base branch.
2. Pull its latest changes from `origin`.
3. Verify that both commands succeed and the working tree remains clean.

If checkout or pull fails, stop and explain the failure. Do not create the feature branch from a potentially outdated or incorrect base.

Do not use destructive Git commands to force the operation.

## Step 6 — Create the feature branch

Create and switch to the selected feature branch using `git checkout -b`.

Verify:
- The current branch matches the intended branch name.
- The working tree is clean.
- The branch was created successfully.

If branch creation fails, stop and report the error. Do not write the spec on another branch.

## Step 7 — Research the codebase

Read the relevant existing project files, including:
- `CLAUDE.md` — roadmap, architecture, and conventions.
- `app.py` — existing routes and application structure.
- `database/db.py` — database schema, connection helper, and query patterns.
- `templates/` — existing templates and inheritance patterns.
- `static/` — existing stylesheets and assets.
- `.claude/specs/` — existing specifications and dependencies.

Use `Glob` to discover actual files before assuming additional files or directories exist.

Inspect related code as necessary to understand the feature's implementation boundaries.

Do not invent routes, database columns, templates, or dependencies without evidence from the codebase or an explicit requirement.

## Step 8 — Write the specification

Generate a Markdown specification with the following exact section structure:

# Spec: <feature_title>

## Overview
One paragraph describing what the feature does and why it belongs at this stage of the Spendly roadmap.

## Depends on
List prerequisite roadmap steps and relevant existing functionality. If there are no dependencies, state "None".

## Routes
List every required new route:
- `METHOD /path` — purpose — access level (public/logged-in).

If no new routes are needed, state "No new routes".

## Database changes
List required tables, columns, constraints, indexes, and relationships.

Verify proposed changes against `database/db.py` and existing application queries.

If no changes are needed, state "No database changes".

## Templates
- **Create:** list new templates and paths.
- **Modify:** list existing templates and the intended changes.

## Files to change
List existing files that need modification and explain why.

## Files to create
List every new file and its purpose.

## New dependencies
List new Python packages and their purpose. If none are required, state "No new dependencies".

## Rules for implementation
Include these mandatory rules:
- No SQLAlchemy or other ORMs.
- Use parameterized SQL queries only.
- Hash passwords using Werkzeug's `generate_password_hash` and verify them with `check_password_hash`.
- Use CSS variables; never hardcode hex color values.
- All page templates must extend `base.html`.
- Follow the existing database connection and transaction patterns.
- Never expose credentials, secrets, or sensitive user data.
- Preserve existing functionality and avoid unrelated changes.

Add any feature-specific constraints supported by the codebase.

## Definition of done
Provide a specific, testable checklist. Every item must be verifiable through an application test, an automated test, or a clearly defined manual verification.

Do not use vague statements such as "feature works correctly".

## Step 9 — Save the spec

Save the specification to:

`.claude/specs/<step_number>-<feature_slug>.md`

Example:

`.claude/specs/02-registration.md`

If `.claude/specs/` does not exist, create the required directory as part of writing the file.

Use `Write` to create the specification.

Do not modify application code, database schemas, existing specifications, or `CLAUDE.md`.

After writing, read the new file back and verify that:
- The content is complete.
- All required sections are present.
- The filename matches the requested step and feature.
- No implementation code was created.

If validation fails, correct the spec before reporting success.

## Step 10 — Report to the user

Only report successful completion after verifying both the branch and spec file.

Print this exact format:

Branch:    <branch_name>
Spec file: .claude/specs/<step_number>-<feature_slug>.md
Title:     <feature_title>

Then tell the user:

"Review the specification at `.claude/specs/<step_number>-<feature_slug>.md`. When ready, enter Plan Mode with Shift+Tab twice to begin implementation."

Do not print the full specification in chat unless explicitly requested.

If any step fails, clearly state what succeeded, what failed, and whether a feature branch was created. Never claim that an operation succeeded unless verified.
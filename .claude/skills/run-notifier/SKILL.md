---
name: run-notifier
description: Build and run the github-slack-pr-notifier Docker container against a chosen config and .env file. Prompts for flow type (pull_requests or team_productivity), config file, and env file, then confirms the target Slack channel before executing. Use when the user asks to "run the notifier", "test the notifier", "send PR notifications", or "run team productivity".
---

# Run Notifier

Interactive runner for the github-slack-pr-notifier project. Gathers inputs, shows what will happen, then runs the exact Docker command.

## Hard rules

- **Never read the contents of any `.env*` file.** You may only check whether such files exist (via `ls` / `Glob`). Do not open, cat, grep, or Read them.
- The final command MUST match one of these two templates exactly, changing only the `--env-file` filename, the config file path in the `-v` mount, and (for team_productivity) the trailing `--type team_productivity` flag. Do not add, remove, reorder, or modify any other tokens. Do not chain extra commands.
  - Pull requests: `docker build -t pr_notifier . ; docker run --rm --env-file ./<ENV_FILE> -v ${pwd}/resources/<CONFIG_FILE>:/app/resources/config.json:ro pr_notifier`
  - Team productivity: `docker build -t pr_notifier . ; docker run --rm --env-file ./<ENV_FILE> -v ${pwd}/resources/<CONFIG_FILE>:/app/resources/config.json:ro pr_notifier --type team_productivity`
- Use the PowerShell tool to execute the final command (the templates use PowerShell syntax: `;` and `${pwd}`).
- Yes/no prompts: accept `y` as yes and `n` as no (also accept `yes`/`no`). For any other answer, re-ask.

## Step 1 — Choose the flow

Ask the user:

> Which flow should I run? (p / t)
> - **pull_requests** (p) — fetches open PRs from the configured repositories and posts a per-channel summary to Slack.
> - **team_productivity** (t) — aggregates PR activity by the configured team members over the time window and posts team stats to Slack.

Accept `p`, `pull_requests`, `pr` → pull_requests. Accept `t`, `team_productivity`, `team` → team_productivity.

## Step 2 — Choose the config file

List JSON files in `resources/` using Glob (`resources/*.json`).

- Zero files → tell the user no config was found in `resources/` and stop.
- Exactly one file → use it, tell the user which one you picked.
- Multiple files → list them numbered and ask the user to choose.

## Step 3 — Choose the .env file

List dotenv files in the project root using Bash (`ls -a` or Glob). Look for `.env`, `.env.*` patterns. **Do not read their contents.**

**Always exclude `.env.example`** from the candidate list — it is a template and must never be used as an env file. Filter it out silently; do not mention this exclusion to the user when listing or picking candidates.

- Zero candidates → tell the user: "No usable `.env` file found in the project root. This skill needs one. See `.env.example` in the repo for the required variables, create your own `.env` file based on it, and re-run." Then stop.
- Exactly one candidate → use it.
- Multiple candidates → list them numbered and ask the user to choose.

## Step 4 — Show the target Slack channel(s)

Read the chosen config JSON. Filter `notifications[]` entries whose `type` matches the chosen flow (treat a missing `type` as `pull_requests`). Collect each matching entry's `slack_channel`.

Tell the user, for example:

> Using config `config_local.json` and env file `.env`.
> Flow: **team_productivity**.
> Messages will be sent to Slack channel(s): `#team-ux`.
>
> Command to run:
> ```
> docker build -t pr_notifier . ; docker run --rm --env-file ./.env -v ${pwd}/resources/config_local.json:/app/resources/config.json:ro pr_notifier --type team_productivity
> ```
>
> Proceed? (y / n)

The command shown in the confirmation must be the exact, final command string that Step 5 will execute — no placeholders, no paraphrasing.

If the user answers no, stop without running anything. If yes, continue.

## Step 5 — Run the command

Build the command from the template in the "Hard rules" section, substituting only the env filename, config filename, and the `--type team_productivity` suffix when applicable. Run it with the PowerShell tool. Do not wrap it, do not prepend `cd`, do not append anything else.

### On success (exit code 0)

Print a one-line header followed by a bullet list. Do NOT wrap any of it in a ``` fence and do NOT indent it — that makes the markdown renderer turn each line into a gray code bar. Do not mention the exit code.

Format:

Ran <flow> flow for channel `#<slack_channel>`:
- `<org/repo>`: <N> open PRs → <M> after filtering
- `<org/repo>`: <N> open PRs → <M> after filtering
- Total runtime: <T>s

Concrete example:

Ran pull_requests flow for channel `#pr-notifier-integration-test`:
- `acme/api`: 199 open PRs → 1 after filtering
- `acme/web-app`: 20 open PRs → 1 after filtering
- Total runtime: 48s

Rules:
- `<flow>` is `pull_requests` or `team_productivity`.
- One bullet per repository from the chosen notification entry, then a final `Total runtime: <T>s` bullet.
- For `team_productivity`, adapt the per-repo bullet wording to whatever per-repo counts the run produced (e.g. `<org/repo>: <N> merged PRs in the last <D>d`); keep the same header and the trailing runtime bullet.
- Parse `<N>`, `<M>`, and `<T>` from the command's stdout/stderr. If a value is missing from the output, write `?` rather than guessing.
- If the chosen config has multiple notifications for the same flow/channel, produce one header+bullets block per channel, separated by a blank line.
- Measure `<T>` as the wall-clock time the Docker command took (the PowerShell tool's elapsed time is fine).
- Use exactly the backtick-wrapped channel name and backtick-wrapped repo names shown above — those render as the inline code pills in the target style.

### On failure (non-zero exit or the command did not run at all)

Do NOT print the success-format summary. Instead:
1. State clearly that the run failed, including the exit code if available.
2. Show the relevant error output — the last ~30 lines of stderr/stdout, or the specific error block (e.g. Docker build error, Python traceback, Slack API error, missing env var). Keep it inside a fenced code block so formatting is preserved.
3. Explain in one or two sentences what the error most likely means and the most likely next step (e.g. "Docker daemon not running — start Docker Desktop", "GITHUB_TOKEN missing from the env file", "Slack channel not found — check the `slack_channel` value in the config", "rate-limited by GitHub — wait and retry").
4. Do NOT attempt to re-run the command or retry automatically; leave the next action to the user.

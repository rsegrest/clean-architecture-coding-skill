# Maintaining this skill

This skill is changed only at the owner's direction. Agents that use it write lessons to
their project's `plan/SKILL-FEEDBACK.md` instead (template: `templates/SKILL-FEEDBACK.md`);
the owner, or an agent the owner directs, folds them in here.

## How a change reaches the harnesses

Harnesses read a released, read-only copy under `/opt/agent-skills/clean-code/`, never
this working tree. Releases use the shared `agent-skill-tools` toolkit.

1. Change the skill on a branch. The pre-commit hook (`git config core.hooksPath
   .githooks`) blocks any commit that fails `skill-lint`.
2. Bump `version:` in `SKILL.md` frontmatter, review, and merge into `main`.
3. Tag the release to match: `git tag vX.Y.Z && git push origin main vX.Y.Z`.
4. Publish it: `sudo skill-release . vX.Y.Z`. This exports the tag, lints it with the
   installed linter against the installed policy, makes it root-owned and read-only,
   and links every installed harness to it. Nothing in the working tree reaches a
   harness until this step.
5. Check: `skill-release --status clean-code`.

Roll back with `sudo skill-release --rollback clean-code vX.Y.Z`. After installing a new
harness, run `skill-release --link clean-code`.

## Size budgets

`skill-policy.json` holds the budgets and the approved `SKILL.md` sections. The
authoritative copy is root-owned at `/etc/agent-skills/clean-code/policy.json`; the linter
takes the stricter of the two, so loosening the repo copy changes nothing. To change the
installed policy deliberately: edit `skill-policy.json`, review the diff, then
`sudo skill-release --set-policy clean-code skill-policy.json`.

Growth past a budget is a review, not an edit: condense or replace text first, and raise
a budget only when the new material earns it.

## Folding feedback in

Read each project's `plan/SKILL-FEEDBACK.md`. For each entry, check its evidence, then
route it to the reference file it names. Reject entries that are session narrative,
restate an existing rule, or have no evidence. Prefer replacing text to adding it.

## One-time setup (the owner runs these)

1. **Close passwordless `sudo` for agent shells.** The release is root-owned; that
   protects nothing if an agent's shell can `sudo` without a password. Check `sudo -l`
   for `NOPASSWD` entries.
2. Install the toolkit (`sudo ./bootstrap.sh vX.Y.Z` in agent-skill-tools), then this
   skill's policy and first release:
   ```sh
   git config core.hooksPath .githooks
   sudo skill-release --set-policy clean-code skill-policy.json
   sudo skill-release . vX.Y.Z
   skill-release --status clean-code
   ```
3. **Optional, per harness:** deny edits to the skill paths in each harness's permission
   settings (in Claude Code, `permissions.deny` entries such as
   `Edit(~/projects/clean-architecture-coding-skill/**)`). A shell command can get around these, so they are an
   extra layer, not the gate.

Harness links live in your home directory, so an agent with your shell could repoint
one. `skill-release --status` flags any link that doesn't point at the release.

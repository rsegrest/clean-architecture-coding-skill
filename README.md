# Clean Code Skill

An agent skill that applies **Robert C. Martin's Clean Code and Clean Architecture
principles** when writing, reviewing, refactoring, scaffolding, or restructuring
code, in TypeScript, Python, Go, Java/Kotlin, C#/.NET, and Rust (with a pattern for
adding others).

It works with Claude Code, Hermes Agent, Pi, OpenCode, Google Antigravity CLI, and
any other agent that supports the `SKILL.md` skill format.

## Sources

The skill summarizes, in its own words, principles from Robert C. Martin's:

- *Clean Code: A Handbook of Agile Software Craftsmanship* (2008; 2nd ed. 2025):
  names, functions, comments, error handling, boundaries, classes, smells
- *Clean Architecture: A Craftsman's Guide to Software Structure and Design* (2017):
  the dependency rule, boundaries, Humble Object, screaming architecture, details
- *Agile Software Development: Principles, Patterns, and Practices* (2002): SOLID
  and the component cohesion/coupling principles
- *Clean Craftsmanship* (2021): TDD, test doubles, simple design
- *Functional Design* (2023): applying SOLID to functional code
- Blog posts at [blog.cleancoder.com](https://blog.cleancoder.com), including "The
  Clean Architecture", "Screaming Architecture", "The Single Responsibility
  Principle", "The Cycles of TDD", and "The Transformation Priority Premise"

Where Martin's advice is contested, notably function size and comments in his
2024–25 [dialogue with John Ousterhout](https://github.com/johnousterhout/aposd-vs-clean-code),
the skill states the shared ground and tells the agent to use judgment. Read the
books; this skill is a working summary, not a substitute.

## What it does

- **Writing code:** test-first where a test setup exists, domain-driven names,
  small focused functions, business rules kept free of I/O, and a self-review
  checklist before handing code back.
- **Reviewing / cleaning up:** findings cite Martin's smell codes (e.g. *G5
  Duplication*, *F3 Flag Arguments*) and SOLID principles, ranked by impact, with
  fixes applied in small, tested steps.
- **New projects:** sizes the architecture to the project, scaffolds layers that
  scream the domain, builds inside-out with one composition root.
- **Restructuring:** audits for tangles, proposes a plan for approval, migrates one
  slice at a time with tests green.
- **Enforcement:** a dependency-free boundary checker for TS/JS and Python, plus
  setup for each language's native tool (dependency-cruiser, import-linter,
  depguard, ArchUnit, NetArchTest, the Cargo crate graph).

## Install

**Protected, multi-harness install (maintainer setup).** The maintainer uses
`agent-skill-tools`, a companion toolkit not yet published, which publishes a
tagged release as a root-owned, read-only copy, lints it against size budgets, and
links every installed harness (Claude Code, Codex, Pi, Grok Build, Qwen Code,
Antigravity CLI, Hermes, and anything reading `~/.agents/skills`) to it. See
[MAINTAINING.md](./MAINTAINING.md).

```bash
sudo skill-release --set-policy clean-code skill-policy.json   # once
sudo skill-release . v1.0.0
```

**Plain install.** Clone the repo into your agent's skills folder. The folder name
should match the skill name, `clean-code`.

| Agent | Global skills folder | Project-level folder |
| :--- | :--- | :--- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Hermes Agent | `~/.hermes/skills/` | n/a (configure an external skills directory) |
| Pi | `~/.pi/agent/skills/` or `~/.agents/skills/` (shared) | `.pi/skills/` or `.agents/skills/` (found by walking up to the repo root) |
| OpenCode | `~/.config/opencode/skills/` (also reads `~/.claude/skills/` and `~/.agents/skills/`) | `.opencode/skills/` (also reads `.claude/skills/` and `.agents/skills/`) |
| Google Antigravity CLI | `~/.gemini/config/skills/` | `.agents/skills/` |

Example (Claude Code):

```bash
git clone git@github.com:rsegrest/clean-architecture-coding-skill.git \
  ~/.claude/skills/clean-code
```

Pi can also install straight from the Git repo:

```bash
pi install git:github.com/rsegrest/clean-architecture-coding-skill
```

> **Upgrading from `clean-architecture`:** the skill was renamed. Rename your
> install folder (e.g. `mv ~/.claude/skills/clean-architecture ~/.claude/skills/clean-code`)
> and update any symlinks.

> **Note:** The Hermes Agent and OpenCode paths come from their public
> documentation and have not been tested with this skill. If a path is wrong,
> please open an issue.

To share one copy across agents, clone once and symlink:

```bash
ln -s ~/.claude/skills/clean-code ~/.hermes/skills/clean-code
```

The agent loads the skill automatically when a request matches, for example
"review this for clean code", "this function is too long, clean it up",
"restructure this app using clean architecture", or "separate the business logic
from the UI". You can also ask for it by name.

## Layout

```text
SKILL.md                              Core ideas, judgment guidance, workflows, index
references/
├─ principles/
│  ├─ clean-code.md                   Names, functions, comments, errors, classes, smells, checklist
│  ├─ solid-and-components.md         SRP/OCP/LSP/ISP/DIP; REP/CCP/CRP; ADP/SDP/SAP
│  ├─ clean-architecture.md           Dependency rule, boundaries, Humble Object, main, details
│  └─ testing.md                      Three laws of TDD, F.I.R.S.T., test doubles, test boundary
├─ refactoring-playbook.md            Step-by-step plan for restructuring an existing project
└─ languages/
   ├─ typescript.md                   Node/Deno/Bun/backends/libraries
   ├─ react.md                        React / React Native / Next.js add-on to typescript.md
   ├─ python.md
   ├─ go.md
   ├─ java-kotlin.md
   ├─ csharp.md
   ├─ rust.md
   └─ adding-a-language.md            Checklist + quick mappings (Swift, Dart, PHP, Ruby, Elixir)
scripts/
└─ check_boundaries.py                Dependency-direction checker (TS/JS + Python)
templates/SKILL-FEEDBACK.md           Where agents record lessons instead of editing the skill
skill-policy.json                     Size budgets and the approved SKILL.md outline
MAINTAINING.md                        Release and feedback process
.githooks/pre-commit                  Runs skill-lint on every commit
```

The skill uses progressive disclosure: the agent always reads `SKILL.md`, then only
the principle and language files the task needs. Adding a language doesn't make
the skill slower or noisier for other languages.

## Boundary checker

```bash
python3 scripts/check_boundaries.py src/
python3 scripts/check_boundaries.py src/ \
  --layers domain=domain usecases=application adapters=infrastructure ui=web,di
python3 scripts/check_boundaries.py src/ --strict   # treat I/O warnings as errors
```

The checker reports:
- **Errors:** an inner layer importing an outer layer, or a domain/use-case file
  importing a framework or I/O library (for example `react`, `axios`,
  `sqlalchemy`, `fastapi`).
- **Warnings:** direct I/O in inner layers (for example `fetch`, `localStorage`,
  `process.env`, `os.environ`).

Exit code `0` means clean, `1` means it found violations. For Go, Java/Kotlin, C#,
and Rust, use the native enforcer described in each language reference.

## Contributing and feedback

Agents using this skill are told not to edit it; they record lessons in their
project's `plan/SKILL-FEEDBACK.md` (template in `templates/`). Changes land through
reviewed pull requests, must pass `skill-lint` (size budgets and the fixed `SKILL.md`
outline in `skill-policy.json`), and bump `version:` in `SKILL.md`.

## Adding a language

Follow `references/languages/adding-a-language.md`, save the result as
`references/languages/<language>.md`, and add a row to the language table in
`SKILL.md`.

## Acknowledgements

The first version of this skill adapted the React layout from
[falsy/react-with-clean-architecture](https://github.com/falsy/react-with-clean-architecture);
its monorepo pattern still informs `react.md`.

## License

MIT

# Clean Architecture Coding Skill

An agent skill that applies **Clean Architecture** when scaffolding new projects
or restructuring existing ones. It is built on the principles of
[falsy/react-with-clean-architecture](https://github.com/falsy/react-with-clean-architecture)
and generalized beyond React.

It works with Claude Code, Hermes Agent, Pi, OpenCode, Google Antigravity CLI,
and any other agent that supports the `SKILL.md` skill format.

## What it does

- **New projects:** sizes the architecture to the project, scaffolds the layers
  (domain → use cases → adapters → frameworks/UI), and builds from the inside out
  with one composition root.
- **Existing projects:** audits the code for tangles, proposes a plan for you to
  approve, then moves the code one feature at a time with tests passing after
  each step.
- **Enforcement:** includes a boundary checker that needs no dependencies, plus
  setup for lint/import rules native to each language.

The core rule: **source dependencies point inward only.** Business rules never
import UI, database, HTTP, or framework code.

## Install

Clone into your global skills folder:

```bash
git clone git@github.com:rsegrest/clean-architecture-coding-skill.git \
  ~/.gemini/config/skills/clean-architecture
```

Or add it to a single project by cloning into `<project>/.agents/skills/clean-architecture`.

The agent loads the skill automatically when a request matches, for example
"restructure this app using clean architecture" or "separate the business logic
from the UI". You can also ask for it by name.

## Layout

```text
SKILL.md                          Core principles, sizing guidance, workflows
references/
├─ typescript-react.md            TS/React/React Native layouts, DI, hooks, enforcement
├─ python.md                      Python layouts (FastAPI/Django/CLI), Protocol ports, import-linter
├─ refactoring-playbook.md        Step-by-step plan for restructuring an existing project
└─ adding-a-language.md           Starting points for Go, Rust, Java/Kotlin, C#, Swift, Dart
scripts/
└─ check_boundaries.py            Dependency-direction checker (TS/JS + Python)
```

Language references use progressive disclosure: the agent reads only the file for
the language it is working in, so adding languages doesn't slow down the skill.

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

Exit code `0` means clean, `1` means it found violations.

## Adding a language

Follow `references/adding-a-language.md`, save the result as
`references/<language>.md`, and add a row to the language table in `SKILL.md`.

## License

MIT

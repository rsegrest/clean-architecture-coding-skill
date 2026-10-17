# Other Languages

For a language without a dedicated reference, map the four layers onto the
language's idioms using this checklist. If the user will use the language
repeatedly, offer to save the result as `references/<language>.md` in this skill
and add it to the table in SKILL.md.

| Concern | Decide |
| :--- | :--- |
| Module boundary | Package / module / crate / namespace / assembly per layer? |
| Port mechanism | Interface, trait, protocol, abstract class, or function type |
| Composition root | `main`, app builder, DI container (only if idiomatic) |
| Plain data types | struct / record / data class for DTOs |
| Enforcement | Compiler module visibility, build-graph rules, or an import linter |
| Test doubles | Hand-written fakes implementing ports |

Quick mappings:

- **Go**: `internal/domain`, `internal/app` (use cases + interfaces defined where
  consumed), `internal/adapters`, `cmd/<app>/main.go` as composition root.
  Enforce with `go-arch-lint` or `depguard`.
- **Rust**: workspace crates `domain`, `application` (traits as ports), `adapters`,
  binary crate wiring. Crate dependencies enforce the rule.
- **Java/Kotlin**: Gradle modules per layer or packages + ArchUnit tests.
- **C#/.NET**: projects `Domain`, `Application`, `Infrastructure`, `Web/Api`;
  project references enforce direction; NetArchTest for checks.
- **Swift**: SPM targets per layer; protocols as ports.
- **Dart/Flutter**: `domain/`, `data/` (repositories), `presentation/`; enforce with
  `import_lint` or package boundaries.

The scripts/check_boundaries.py checker supports TS/JS and Python only; for other
languages, rely on the native enforcer.

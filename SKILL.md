---
name: clean-code
description: >-
  Applies Robert C. Martin's Clean Code, SOLID, component, and Clean Architecture
  principles when writing, reviewing, refactoring, scaffolding, or restructuring code.
  Use when the user asks for "clean code", a code review or cleanup, better names or
  smaller functions, SOLID, TDD, separating business logic from UI/database/framework
  code, ports and adapters, a layered or "screaming" folder structure, or checking for
  dependency/layer violations. Covers TypeScript (plus a React add-on), Python, Go,
  Java/Kotlin, C#/.NET, and Rust, with a pattern for adding other languages.
---

# Clean Code & Clean Architecture

Grounded in Robert C. Martin's books: *Clean Code* (2008; 2nd ed. 2025), *Clean
Architecture* (2017), *Agile Software Development: Principles, Patterns, and
Practices* (2002), *Clean Craftsmanship* (2021), and *Functional Design* (2023), plus
his blog posts at blog.cleancoder.com. The principle references below summarize them
by chapter; read the one that fits the task before acting.

## The two ideas everything else serves

1. **Code is read far more than it is written. Optimize for the reader.** Names
   reveal intent, functions do one thing at one level of abstraction, and tests let
   anyone change the code without fear. (*Clean Code*)
2. **Source dependencies point inward, toward policy.** Business rules never import
   UI, database, web, or framework code; those are details that plug into the
   rules. (*Clean Architecture*, ch. 22)

```text
 frameworks & drivers   (web/UI framework, DB driver, HTTP client, CLI, main)
   └─> interface adapters (controllers, presenters, gateways/repositories)
         └─> use cases      (application business rules + port interfaces)
               └─> entities  (enterprise business rules and data)
```

## Principle references (read the one(s) the task needs)

| Read this | When |
| :--- | :--- |
| [principles/clean-code.md](./references/principles/clean-code.md) | Writing or reviewing any code: names, functions, comments, formatting, objects vs. data, errors, boundaries, classes, smells |
| [principles/solid-and-components.md](./references/principles/solid-and-components.md) | Designing classes/modules/packages; SRP/OCP/LSP/ISP/DIP; package cohesion and coupling; breaking dependency cycles |
| [principles/clean-architecture.md](./references/principles/clean-architecture.md) | Layering, boundaries, ports & adapters, Humble Object, composition root, "the database/web/framework is a detail" |
| [principles/testing.md](./references/principles/testing.md) | TDD, test design, test doubles, the test boundary, simple design |
| [refactoring-playbook.md](./references/refactoring-playbook.md) | Restructuring an existing project toward Clean Architecture |

## Language references (load only the one you need)

| Language / stack | Reference |
| :--- | :--- |
| TypeScript / JavaScript (Node, Deno, Bun, libraries, backends) | [languages/typescript.md](./references/languages/typescript.md) |
| React, React Native, Next.js (read typescript.md first) | [languages/react.md](./references/languages/react.md) |
| Python | [languages/python.md](./references/languages/python.md) |
| Go | [languages/go.md](./references/languages/go.md) |
| Java / Kotlin | [languages/java-kotlin.md](./references/languages/java-kotlin.md) |
| C# / .NET | [languages/csharp.md](./references/languages/csharp.md) |
| Rust | [languages/rust.md](./references/languages/rust.md) |
| Anything else (Swift, Dart, PHP, Ruby, ...) | [languages/adding-a-language.md](./references/languages/adding-a-language.md) |

Language idioms win over generic rules when they conflict (e.g. C# names interfaces
`IThing`, Go prefers short receiver names). Martin's rules are about intent; apply
the intent in the language's idiom.

## Judgment: size the response to the code

Martin presents his rules as heuristics, not laws, and *Clean Architecture* itself
recommends partial boundaries and YAGNI. Apply them in proportion:

- **Scripts, prototypes, < ~1k LOC, no real business rules** → Clean Code basics
  only (names, small focused functions, no I/O mixed into logic). No layers. Say so.
- **Medium apps** → one package, four layers, ports only at real I/O boundaries
  (DB, network, file system, clock, randomness, third-party SDKs).
- **Large / multi-client apps** → layers as separately built packages, modules,
  crates, or projects, so the build enforces the dependency rule.
- Don't create an interface that has one trivial implementation and no test-double
  need. Ports exist for boundaries, not for every class.
- Prefer functions small enough to read at a glance, but don't split a coherent
  piece of logic into fragments the reader must reassemble. Each extracted function
  must earn its name. (Martin and John Ousterhout debated this in 2024–25; the
  shared ground is "one thing, one level of abstraction, readable at a glance".)
- Comments that explain *why*, warn of consequences, or document a public API are
  good comments in Martin's own taxonomy. Delete the ones that restate the code.
- Never refactor unrelated code the user didn't ask about. Mention it instead.

## Workflow A: Writing new code (default discipline)

1. If the project has a test setup, follow TDD (Martin's three laws, see
   testing.md): failing test → minimal code → refactor. If it has none, offer to
   add one; don't force it on a throwaway script.
2. Name things for the domain (see clean-code.md "Names").
3. Keep business rules free of I/O and framework types; pass them plain data.
4. Before finishing, run the self-review checklist at the end of clean-code.md.

## Workflow B: Review or clean up existing code

1. Read the surrounding code first and match its conventions unless they're the
   problem being fixed.
2. Use the smell list in clean-code.md and the SOLID checks in
   solid-and-components.md. Cite the smell (e.g. "G5 Duplication", "F3 Flag
   Argument") and the concrete fix.
3. Rank findings: dependency-rule violations and missing tests first, then design
   (SRP/DIP), then function/naming issues, then formatting (leave formatting to the
   formatter).
4. When applying fixes: make sure tests cover the code first (add characterization
   tests if not), change in small steps, run tests after each. Leave the code
   cleaner than you found it (the Boy Scout Rule), but within the scope asked.

## Workflow C: New project

1. **Clarify the domain**: core entities and the user-facing actions (these become
   use cases). Ask if unclear.
2. **Choose scale** (Judgment, above) and confirm the layout with the user. Folders
   should "scream" the domain (`orders/`, `billing/`), not the framework
   (*Clean Architecture*, ch. 21).
3. **Load the language reference** and scaffold.
4. **Build inside-out, test-first**: entities → use cases with ports, tested with
   in-memory fakes → adapters → delivery mechanism (UI/HTTP/CLI) → `main`
   (composition root).
5. **Add boundary enforcement** from the language reference to CI.
6. **Verify**: entity and use-case tests run with no framework, network, or DB.

## Workflow D: Restructure an existing project

Follow [refactoring-playbook.md](./references/refactoring-playbook.md): audit → map →
agree on the target with the user → move one slice at a time with tests green →
enforce → verify. Never do a big-bang rewrite unless the user explicitly asks.

## Validation

- For TS/JS and Python, run the bundled checker from the project root, using this
  skill's directory:
  `python3 <skill-dir>/scripts/check_boundaries.py <src-dir>`
  Use `--layers` to map custom folder names, e.g.
  `--layers domain=domain,entities usecases=application,use_cases adapters=adapters,infrastructure ui=ui,web,di`.
  Exit code 0 means no dependency-rule violations.
- For every language, also install the native enforcer from the language
  reference so CI catches regressions.
- The build, linter, formatter, and full test suite pass.

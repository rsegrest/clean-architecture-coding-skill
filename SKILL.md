---
name: clean-architecture
description: >-
  Applies Clean Architecture (domain / use cases / adapters / frameworks, inward-only
  dependencies, ports & adapters, a single composition root) when scaffolding new
  projects or restructuring, rearchitecting, untangling, or auditing existing ones.
  Use when the user asks to "use clean architecture", separate business logic from UI
  or database code, make code testable without the framework, plan a layered folder
  structure, or check for layer/dependency violations. Covers TypeScript/React and
  Python, with a pattern for adding other languages.
---

# Clean Architecture

Based on the principles of
[react-with-clean-architecture](https://github.com/falsy/react-with-clean-architecture)
(Rick's fork: `rsegrest/react-with-clean-architecture`), generalized beyond React.

## The one rule

**Source dependencies point inward only.** Inner layers never import, name, or
know about outer layers. Everything else follows from this.

```text
 frameworks / UI / main   (React, FastAPI, CLI, DB drivers, HTTP clients)
   └─> adapters            (repositories, presenters, infrastructure wrappers)
         └─> use cases      (application logic + port interfaces)
               └─> domain    (entities, aggregates, value objects, domain rules)
```

| Layer | Contains | May depend on | Must NOT contain |
| :--- | :--- | :--- | :--- |
| **Domain** | Entities, aggregates, value objects, pure domain rules, DTO types | Nothing (std lib only) | Framework imports, I/O, HTTP, DB, UI, env vars |
| **Use cases** | One class/function per app action; **port interfaces** (e.g. `BoardRepository`) | Domain | Concrete repositories, fetch/requests, ORM, React/state libs |
| **Adapters** | Repositories implementing ports, presenters/view-model mappers, infra wrappers (`Http`, `Storage`) | Use cases, domain | Business decisions, UI rendering |
| **Frameworks / UI** | Components, routes/controllers, hooks, state store, CLI, **composition root (DI)** | Everything inward | Business rules, direct DB/HTTP calls |

Key mechanics:

- **Dependency inversion**: a use case needs data → it declares a port
  (interface/Protocol) in the use-case layer; an adapter implements it; the
  composition root wires them together. The use case never imports the adapter.
- **Composition root**: exactly one place (e.g. `di/`, `main.py`, `container.ts`)
  constructs concrete adapters and injects them. This is the only module allowed
  to know about every layer.
- **Data crossing boundaries** is plain data (DTOs/entities), never ORM rows, HTTP
  responses, or framework objects.
- **Presenters / view models** turn domain output into UI-friendly shapes so
  components stay dumb.

## Pragmatism (read before applying)

Clean Architecture costs indirection. Scale it to the project:

- **Scripts, prototypes, < ~1k LOC, or no real business rules** → don't apply the
  full structure. At most, keep I/O out of pure logic functions. Say so to the user.
- **Medium apps** → single package, four top-level folders, ports only where a real
  external dependency exists (DB, HTTP, storage, clock, randomness).
- **Large / multi-client apps** (web + mobile, API + worker) → separate packages per
  layer (monorepo), sharing `domain` and `adapter` packages across clients.
- Don't create an interface with exactly one trivial implementation *and* no test
  double need. Ports exist for I/O boundaries, not for every class.
- Feature-sliced folders (`features/board/{domain,application,adapters,ui}`) are
  fine; the dependency rule matters, not the folder names.

## Workflow A: New project

1. **Clarify the domain**: list core entities and the user-facing actions (these
   become use cases). Ask the user if unclear.
2. **Choose scale** (see Pragmatism) and confirm the layout with the user.
3. **Load the language reference** (below) and scaffold the folders.
4. **Build inside-out**: domain entities + tests → use cases with ports + tests using
   in-memory fakes → adapters → UI → composition root.
5. **Add boundary enforcement** (lint rule / import contract from the language
   reference) and run [check_boundaries.py](./scripts/check_boundaries.py).
6. **Verify**: domain and use-case tests run with no framework, network, or DB.

## Workflow B: Restructure an existing project

Follow [references/refactoring-playbook.md](./references/refactoring-playbook.md).
Summary: audit → map → agree on target with user → move incrementally (strangler
style, tests green at every step) → enforce boundaries → verify. Never do a big-bang
rewrite unless the user explicitly asks.

## Language references (load only the one you need)

| Language / stack | Reference |
| :--- | :--- |
| TypeScript, React, React Native, Node | [references/typescript-react.md](./references/typescript-react.md) |
| Python (FastAPI, Django, Flask, CLI, scripts) | [references/python.md](./references/python.md) |
| Any other language | [references/adding-a-language.md](./references/adding-a-language.md) |

## Validation

- Run the generic checker (TS/JS/Python) from the project root:
  `python3 ~/.gemini/config/skills/clean-architecture/scripts/check_boundaries.py <src-dir>`
  Use `--layers` to map custom folder names, e.g.
  `--layers domain=domain,entities usecases=application,use_cases adapters=adapters,infrastructure ui=ui,components,web`.
  Exit code 0 = no inward-rule violations.
- Prefer also installing the language-native enforcer listed in the reference so CI
  catches regressions.
- Confirm domain/use-case tests pass with no framework, network, or DB.

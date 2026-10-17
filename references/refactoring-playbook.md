# Refactoring Playbook: Moving an Existing Project to Clean Architecture

Goal: incremental, always-shippable migration. Tests stay green after every step.

## 1. Audit (read-only)

- Identify stack, entrypoints, test setup, and how the app is run/built.
- Run [check_boundaries.py](../scripts/check_boundaries.py) if folders already
  resemble layers; otherwise grep for the tangles:
  - UI files calling `fetch`/`axios`/ORM/SQL/`localStorage`/env vars directly.
  - Business rules (validation, pricing, permissions, state transitions) inside
    components, route handlers, views, or ORM models.
  - Framework types (ORM rows, request objects, Pydantic/Prisma models) passed deep
    into logic.
  - Global singletons (DB clients, API clients) imported everywhere.
- Note test coverage around the hot spots. If thin, add characterization tests
  before moving code.

## 2. Map and propose (get user sign-off)

Produce a short plan (artifact) containing:
- Current → target layer for each major module/folder.
- Entities and use cases discovered.
- Ports needed (one per external dependency: DB, HTTP API, storage, clock, auth).
- Chosen scale (see Pragmatism in SKILL.md) and folder layout.
- Ordered migration slices (one feature or use case per slice), riskiest last.

Do not start moving files until the user approves.

## 3. Migrate one slice at a time

For each slice (e.g. "board loading"):
1. Create the target folders if missing; add path aliases / package config.
2. **Extract domain**: move pure rules into entities/functions; add unit tests.
3. **Define the port** in the use-case layer from what the logic actually needs
   (not from what the current client exposes).
4. **Write the use case** using the port; test with an in-memory fake.
5. **Wrap existing I/O code as an adapter** implementing the port. Reuse the old
   code; don't rewrite it.
6. **Wire in the composition root** and switch the UI/route to call the use case.
7. Delete the now-dead direct calls. Run all tests and the build.
8. Commit with a message naming the slice.

Keep old and new paths side by side only during a slice; never leave a slice
half-migrated across commits.

## 4. Enforce

After the first slice lands, add the language-native boundary rule (see language
reference) scoped to migrated folders, and widen the scope as slices complete. This
prevents regressions while migration is ongoing.

## 5. Verify and report

- Full test suite + build pass; boundary checker exits 0.
- Domain/use-case tests run with no network, DB, or framework.
- Summarize to the user: slices done, remaining slices, any deliberate exceptions.

## Anti-patterns to avoid

- Big-bang move of every file in one commit.
- Creating ports/interfaces for pure in-process helpers.
- Anemic use cases that just forward to a repository while the rules stay in the UI.
- Leaking ORM/HTTP/framework types through ports.
- Multiple composition roots or service locators sprinkled through components.

# Testing and TDD

From Robert C. Martin, *Clean Code* ch. 9, *Clean Craftsmanship* (2021) part I,
*Clean Architecture* ch. 28, and the blog posts "The Cycles of TDD" (2014) and "The
Transformation Priority Premise" (2013).

## The three laws of TDD

1. Don't write production code until you have a failing test.
2. Don't write more of a test than is sufficient to fail (failing to compile
   counts as failing).
3. Don't write more production code than is sufficient to pass the current
   failing test.

Then the **Red → Green → Refactor** cycle: make it fail, make it pass, make it
clean. Refactoring is not optional; it's the step that keeps the design clean.

Agent practice: run the test and *see* it fail for the expected reason before
writing the implementation. Report the red and green runs to the user.

## Clean tests

- Test code is held to the same standard as production code. Dirty tests become a
  liability and are eventually deleted, and then the production code rots.
- **Readability** is the top priority. Structure each test as
  **Build–Operate–Check** (Arrange–Act–Assert, Given–When–Then).
- Grow a small **domain-specific testing language** (helper functions like
  `givenAccountWithBalance(100)`) so tests read as specifications.
- **One concept per test.** Multiple asserts are fine if they verify one behavior.

## F.I.R.S.T.

- **Fast**: run them constantly. Core-logic tests take milliseconds.
- **Independent**: no test depends on another's state or order.
- **Repeatable**: same result in any environment, offline included.
- **Self-validating**: pass or fail, with no log reading.
- **Timely**: written just before the production code.

## Test doubles (*Clean Craftsmanship*)

From least to most behavior: **dummy** (passed, never used) → **stub** (returns
canned values) → **spy** (stub that records calls) → **mock** (spy that knows
what it expects) → **fake** (working simplified implementation, e.g. in-memory
repository).

- Prefer **hand-written fakes and stubs implementing your ports** over mocking
  libraries. They're simpler, refactor-safe, and document the port.
- Use spies and mocks only for verifying an interaction that *is* the behavior
  (e.g. "an email was sent").
- **Don't mock what you don't own.** Wrap third-party APIs in an adapter and test
  the adapter with integration tests; fake the port everywhere else.

## Test strategy by layer

| Layer | Test type | Doubles |
| :--- | :--- | :--- |
| Entities | Plain unit tests | None needed |
| Use cases | Unit tests through the use-case API | Fakes for output ports |
| Adapters | Integration tests against real or containerized services | None (that's the point) |
| Delivery / UI | A few end-to-end or component tests | Test composition root |

## The test boundary (*Clean Architecture* ch. 28)

Tests are the outermost circle. Couple tests to **behavior through a stable testing
API** (use cases, public module surface), not to private structure, so refactoring
doesn't break them (the "fragile tests problem").

## Transformation Priority Premise (TPP)

When making a failing test pass, prefer the simplest transformation that works.
Martin's list runs roughly from nil → constant → variable, through adding
conditionals, collections, recursion, and iteration, with assignment (mutating
state) last. Each new test forces the code to become a little more general. If
passing a test needs a big jump, write a smaller test first.

## Legacy code without tests

Before refactoring untested code, add **characterization tests** that pin current
behavior (including odd behavior), then refactor in small steps with the tests
green.

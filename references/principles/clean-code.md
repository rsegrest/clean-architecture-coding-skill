# Clean Code

Summarized from Robert C. Martin, *Clean Code* (2008, chapters noted; the 2025 second
edition keeps these foundations and adds design, architecture, and AI-assisted
coding). The paraphrases are ours; see the book for the full argument and examples.

The standard: **clean code reads like well-written prose and does what the reader
expects.** Every rule below serves that.

## Names (ch. 2)

- **Reveal intent.** A name says why it exists, what it does, and how it's used. If
  it needs a comment, rename it. `elapsedDays`, not `d`.
- **Avoid disinformation.** Don't call something `accountList` unless it is a list.
  Avoid names that differ only slightly (`XYZControllerForHandlingOfStrings` vs.
  `XYZControllerForStorageOfStrings`).
- **Make meaningful distinctions.** No `a1`/`a2`, no noise words (`ProductInfo` vs.
  `ProductData`, `theMessage`).
- **Pronounceable and searchable.** Single letters only for tiny local scopes.
  Name length grows with scope size (N5).
- **No encodings.** No Hungarian notation or member prefixes (`m_`). Follow the
  language convention where one exists (C# `IThing`, Go exported capitals).
- **Classes/types are nouns** (`Customer`, `AddressParser`); avoid vague nouns like
  `Manager`, `Processor`, `Data`, `Info`. **Functions are verbs** (`postPayment`,
  `deletePage`, `isPosted`).
- **One word per concept.** Don't mix `fetch`, `retrieve`, and `get` for the same
  idea. Don't reuse one word for two concepts.
- **Use solution-domain names** for technical concepts (`JobQueue`, `Visitor`) and
  **problem-domain names** for business concepts. Business code should read in the
  language a domain expert uses.

## Functions (ch. 3)

- **Small.** Readable at a glance; blocks inside `if`/`while` are often one call.
- **Do one thing.** A function does one thing if you can't extract another function
  from it with a name that isn't just a restatement of its implementation.
- **One level of abstraction per function.** Don't mix `getHtml()` with
  `.append("\n")`. Order functions top-down so each is followed by those at the next
  level down (the *stepdown rule*).
- **Switch statements** on a type belong in one place: a factory that creates
  polymorphic objects. Don't repeat the same switch across the code (G23).
- **Arguments:** zero is ideal, one or two are fine, three need justification, more
  means an object is missing (F1). No **flag arguments** (F3): a boolean parameter
  announces the function does two things; split it. Avoid **output arguments** (F2).
- **No hidden side effects.** `checkPassword` must not also initialize a session.
- **Command-query separation.** A function either changes state or answers a
  question, not both.
- **Prefer exceptions to error codes** (in languages that use them; see the
  language reference). Extract the body of a `try` into its own function; error
  handling is "one thing".
- **Don't repeat yourself** (G5). Duplication is the root of much design rot.
- Delete dead functions (F4).

## Comments (ch. 4)

Comments compensate for failing to express ourselves in code. Try the code first.

- **Good:** legal headers; explanation of intent or a non-obvious decision;
  clarification of an unchangeable API's meaning; warnings of consequences; TODOs
  with an owner or ticket; doc comments on public APIs.
- **Bad:** redundant (restates the code); misleading or obsolete (C2); mandated
  boilerplate; journal/changelog comments (that's version control's job); noise;
  position markers and closing-brace comments; attributions; **commented-out code
  (C5): delete it.**

## Formatting (ch. 5)

- Adopt the language's standard formatter and let it settle every argument.
- **Newspaper metaphor:** high-level concepts at the top of a file, details below.
- Related code close together (vertical density); blank lines between concepts.
  Declare variables near use; put callers just above callees.
- A team agrees on one style; consistency beats personal preference.

## Objects and data structures (ch. 6)

- **Objects hide data and expose behavior. Data structures expose data and have no
  meaningful behavior.** Both are valid. Choose deliberately:
  - Procedural code over data structures makes adding *functions* easy.
  - OO code makes adding *types* easy.
- **Avoid hybrids** that are half object, half data structure.
- **Law of Demeter:** a method talks to its own fields, its parameters, objects it
  creates, and nothing beyond. `a.getB().getC().doThing()` is a train wreck (G36).
  Tell the object to do the work instead. (Chaining over plain data structures or
  fluent builders isn't a violation.)
- DTOs are honest data structures; that's what crosses architectural boundaries.

## Error handling (ch. 7)

- Use exceptions (or the language's idiomatic error type) rather than return codes
  the caller can forget.
- Write the `try/catch/finally` first when code can fail; it defines the scope.
- Prefer **unchecked** exceptions; checked exceptions break encapsulation by forcing
  every intermediate layer to know about a low-level failure.
- Give exceptions context: what operation failed and why.
- **Define exception types by how the caller handles them.** Wrap a third-party API
  so callers deal with one exception type you own.
- **Special Case pattern:** return an object that handles the special case instead
  of making callers check.
- **Don't return null. Don't pass null.** Return empty collections, special-case
  objects, or the language's option type.

## Boundaries (ch. 8)

- **Wrap third-party code.** Don't pass a `Map` or SDK object around the system;
  wrap it in a class that exposes only what your code needs.
- Write **learning tests** against third-party APIs; they double as upgrade checks.
- **Code against the interface you wish you had** when the other side doesn't exist
  yet, then write an adapter. This is the code-level form of a port.

## Classes (ch. 10)

- Order: constants, fields, then public functions, each followed by the private
  helpers it uses (stepdown).
- **Small, measured in responsibilities.** If you can't name a class without "and",
  "or", "Manager", or "Processor", it has too many. Single Responsibility (see
  solid-and-components.md).
- **Cohesion:** methods use most of the fields. When a subset of methods uses a
  subset of fields, a smaller class is waiting to be extracted.
- **Organize for change:** new behavior arrives as new classes, not edits to old
  ones (OCP). Depend on abstractions to isolate from change (DIP).

## Systems (ch. 11)

- **Separate construction from use.** Build the object graph in `main` (or a
  composition root/DI container) and hand it to the application, which never
  constructs its own dependencies.
- Keep cross-cutting concerns (transactions, logging, auth) out of business code
  using decorators, middleware, or aspects.

## Emergence: simple design (ch. 12, after Kent Beck)

In priority order, a design is simple when it:
1. Runs all the tests (passes them).
2. Contains no duplication.
3. Expresses the intent of the programmer.
4. Minimizes the number of classes and methods.

Rule 4 is the lowest priority but real: don't create classes and interfaces out of
dogma.

## Concurrency (ch. 13)

- Keep concurrency code separate from other code (SRP).
- Limit the scope of shared data; prefer copies and immutable data.
- Keep synchronized sections small; know your library's thread-safe collections.
- Make threaded code pluggable so the logic is tested single-threaded first.

## Smells and heuristics (ch. 17, selected)

Cite these by code in reviews.

| Code | Smell | Fix |
| :--- | :--- | :--- |
| C3 / C5 | Redundant comment / commented-out code | Delete |
| E1 / E2 | Build or tests need more than one step | One command for each |
| F1 | Too many arguments | Introduce a parameter object or split |
| F2 | Output arguments | Return a value or change the object's own state |
| F3 | Flag arguments | Split into two functions |
| F4 | Dead function | Delete |
| G5 | Duplication | Extract function/class; replace repeated switch with polymorphism |
| G6 | Code at the wrong level of abstraction | Move details down, concepts up |
| G9 | Dead code | Delete |
| G14 | Feature envy (method uses another class's data more than its own) | Move the method |
| G23 | If/else or switch on type, repeated | Polymorphism behind a factory |
| G25 | Magic numbers | Named constants |
| G28 | Unencapsulated conditional | `if (shouldBeDeleted(timer))` |
| G29 | Negative conditional | `if (buffer.shouldCompact())`, not `if (!buffer.shouldNotCompact())` |
| G30 | Function does more than one thing | Extract |
| G31 | Hidden temporal coupling | Make order explicit via arguments/returns |
| G34 | Function descends more than one level of abstraction | Extract the lower level |
| G35 | Configurable data buried low | Pass config in from the top |
| G36 | Transitive navigation (train wrecks) | Tell, don't ask |
| N1 | Non-descriptive name | Rename |
| N5 | Short name for a long scope | Lengthen with scope |

## Self-review checklist (run before handing code back)

- [ ] Every name reads correctly to someone who knows the domain but not the code.
- [ ] Each function does one thing at one level of abstraction; no flag arguments.
- [ ] No duplication introduced; no dead or commented-out code.
- [ ] Errors use the language's idiom, carry context, and never return/pass null.
- [ ] Third-party types are wrapped at the boundary, not passed through the core.
- [ ] Business rules don't import framework, DB, HTTP, UI, or env access.
- [ ] Tests cover the change and run fast with no I/O for core logic.
- [ ] Formatter and linter pass.

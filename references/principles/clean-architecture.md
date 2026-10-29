# Clean Architecture

From Robert C. Martin, *Clean Architecture* (2017), parts V–VI, and his blog posts
"Screaming Architecture" (2011) and "The Clean Architecture" (2012).

## Purpose

The goal of architecture is to **minimize the human effort needed to build and
maintain the system.** Good architecture keeps options open by keeping *policy*
(business rules) independent of *details* (I/O, frameworks, delivery). Decisions
about databases, web frameworks, and servers can then be deferred, and changed.

## The Dependency Rule (ch. 22)

**Source code dependencies must point only inward, toward higher-level policy.**
Nothing in an inner circle may name anything in an outer circle: no functions,
classes, variables, or data formats.

| Circle | Contains | Knows about |
| :--- | :--- | :--- |
| **Entities** | Enterprise-wide critical business rules and data. Would exist even without software. | Nothing outward |
| **Use cases** | Application-specific business rules. Orchestrate entities; define input/output **ports** (interfaces) and request/response models. | Entities |
| **Interface adapters** | Controllers, presenters, gateways/repositories. Convert data between use-case format and external format (SQL, HTTP, view models). | Use cases, entities |
| **Frameworks & drivers** | Web framework, UI framework, DB driver, HTTP client, CLI, devices, `main`. Glue code only. | Everything inward |

Four circles is a convention, not a rule. Some systems need more or fewer; the
dependency rule is what matters.

"Level" = distance from inputs and outputs. The further from I/O, the higher the
level and the more stable and protected the code should be (ch. 19).

## Crossing boundaries

- When flow of control goes outward (a use case needs to save data or present a
  result), use **dependency inversion**: the use case calls an interface it owns
  (output port); an outer-layer class implements it.
- **Data that crosses a boundary is simple, isolated data structures**: DTOs,
  request/response models, plain structs. Never ORM rows, HTTP request objects, or
  framework types. Don't pass entities outward as if they were response models;
  map them.

## Business rules (ch. 20)

- **Entity**: critical business data plus the critical rules operating on it
  (e.g. `Loan` with principal, rate, and `makePayment`). Pure, framework-free.
- **Use case**: one application-specific operation (e.g. "apply for loan"). Takes
  a request model, returns a response model, enforces application rules, and calls
  entities and output ports. Doesn't know about HTML, SQL, or HTTP.

## Screaming architecture (ch. 21)

The top-level structure should **tell you what the system does, not which framework
it uses.** A health-care app's folders should say `patients/`, `appointments/`,
`billing/`, not `controllers/`, `models/`, `views/`. The framework is a tool, not
the architecture. Use cases should be testable without the framework running.

## Humble Object (ch. 23)

Split behavior at a boundary into a **humble** part (hard to test: GUI, DB driver,
network) and a **testable** part. Make the humble part so simple it doesn't need
tests.

- **Presenter / View:** the presenter turns response models into a view model of
  strings, flags, and formatted values; the view only displays it.
- **Gateway / repository:** the interface is in the use-case layer; the
  implementation is a humble SQL/HTTP wrapper.
- **Service listeners:** a humble listener receives external data and converts it
  to plain data for the use case.

## Partial boundaries (ch. 24)

Full boundaries (separate components, reciprocal interfaces) are expensive. Cheaper
alternatives, in increasing order of decay risk:

1. **Skip the last step**: separate interfaces and modules, built and deployed
   together.
2. **One-dimensional boundary / Strategy**: a single interface the client uses.
3. **Facade**: a class that delegates; no inversion at all.

Pick the cheapest one that protects the parts actually likely to change, and
upgrade it when it starts to hurt (YAGNI, ch. 25).

## The Main component (ch. 26)

`main` is the dirtiest, lowest-level plugin: it creates factories, strategies,
configuration, and concrete adapters, injects them, and hands control to the
high-level policy. **It is the only place that knows every concrete type.** Have
one per deployment configuration (dev, test, prod) if needed. This is the
*composition root*.

## Services are not architecture (ch. 27)

Splitting into microservices does not decouple anything by itself. Services that
share data schemas or must all change for one feature (the "kitty problem") are
coupled. Each service still needs internal Clean Architecture, and cross-cutting
features need plugin points inside services.

## The Test Boundary (ch. 28)

Tests are the outermost circle: they depend inward and nothing depends on them.
Tests coupled to UI structure or internals are fragile. Give tests a **testing
API** (often the use cases themselves) so behavior can be verified without the GUI
or DB.

## Details (part VI)

- **The database is a detail** (ch. 30). The data model matters; the storage
  technology doesn't. Keep SQL and ORM types behind gateways.
- **The web is a detail** (ch. 31). It's an I/O device. Keep business rules
  unaware of HTTP, sessions, and rendering.
- **Frameworks are details** (ch. 32). Marrying a framework is an asymmetric
  relationship: you commit to it and it doesn't commit to you. Keep framework
  annotations, base classes, and types out of entities and use cases; derive from
  framework classes only in the outer circle.

## Packaging (ch. 34, by Simon Brown)

The same architecture can be packaged by layer, by feature, as ports and adapters,
or by component. Whichever you choose, **use the language's visibility rules
(non-public types, internal packages, module exports) so the compiler enforces the
boundaries**; good intentions alone decay.

## Pragmatics

- Start with the dependency rule and use cases. Add boundaries where the code
  actually crosses I/O or volatility lines.
- Ports exist for things that are I/O, volatile, or need a test double: DB,
  network, file system, clock, random/IDs, message bus, third-party SDKs.
- "Feature-sliced" layouts (`orders/{domain,application,adapters,web}`) satisfy
  the rule and scream the domain. Prefer them over layer-first at scale.
- Anemic use cases that just forward to a repository, while rules still live in
  controllers, are the most common way this goes wrong.

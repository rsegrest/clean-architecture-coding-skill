# SOLID and Component Principles

From Robert C. Martin, *Agile Software Development: Principles, Patterns, and
Practices* (2002), where these principles were first collected, restated in *Clean
Architecture* (2017) parts III–IV and the blog post "The Single Responsibility
Principle" (2014). *Functional Design* (2023) shows they apply to functional code
too: replace "class" with "module" or "group of functions".

## SOLID: arranging functions and data into classes/modules

### SRP: Single Responsibility Principle

**A module should be responsible to one, and only one, actor.** An actor is a group
of people (a role, a department) who would request a change. It is *not* "a module
does one thing"; that's the rule for functions.

Martin's summary: gather together the things that change for the same reasons;
separate the things that change for different reasons.

- Smell: `Employee` has `calculatePay()` (Accounting), `reportHours()` (HR), and
  `save()` (DBAs). Three actors, so a change for one can break another.
- Fix: separate the data from the behaviors (`PayCalculator`, `HourReporter`,
  `EmployeeSaver` over plain `EmployeeData`), optionally behind a facade.
- Watch for merge conflicts and accidental duplication. Two identical-looking code
  paths that serve different actors are *not* duplication; merging them couples the
  actors.

### OCP: Open-Closed Principle

**A module should be open for extension but closed for modification.** New
behavior arrives by adding code, not editing working code.

- Architectural form: arrange components so that higher-level policy is protected
  from changes in lower-level details. Arrows point toward what you want to
  protect.
- Tools: polymorphism, strategy, plugin points, dependency inversion.
- Don't predict every extension; apply OCP to the axes of change you've actually
  seen (or that the requirements name).

### LSP: Liskov Substitution Principle

**Subtypes must be substitutable for their base types without the caller
noticing.**

- Classic violation: `Square extends Rectangle`; setting width independently breaks
  callers' expectations.
- Applies to interfaces and services too: if every implementation of a port
  (or every REST provider) doesn't honor the same contract, callers fill up with
  `if (provider == X)` special cases.
- Signs of violation: type checks/casts on the subtype, implementations that throw
  `NotSupported`, overridden methods that weaken postconditions.

### ISP: Interface Segregation Principle

**Don't force clients to depend on things they don't use.**

- Split fat interfaces into role interfaces per client (`OrderReader`,
  `OrderWriter`).
- In architecture: don't depend on a framework or service that drags in far more
  than you need; its baggage becomes your risk.

### DIP: Dependency Inversion Principle

**Source code dependencies should refer to abstractions, not concretions,** at
least for anything volatile.

- Stable things (the standard library, the language) are fine to depend on
  concretely. Volatile things (your own fast-changing modules, I/O, frameworks)
  should be reached through abstractions.
- Rules of thumb: don't refer to volatile concrete classes; don't derive from them;
  don't override concrete functions; never mention the name of anything concrete
  and volatile in policy code.
- Creation of concretes goes in factories or the composition root (`main`).
- **The abstraction belongs to the client.** The use case owns the
  `OrderRepository` interface; the database adapter implements it. That ownership
  is what makes the dependency arrow point inward.

## Component principles: arranging modules into packages

A *component* is the unit of deployment or release: a jar, DLL, gem, npm package,
Go module, Rust crate, or Python distribution. In a single-package app, apply the
same thinking to top-level folders.

### Cohesion: what goes in a component

| Principle | Statement | Pulls toward |
| :--- | :--- | :--- |
| **REP**: Reuse/Release Equivalence | The unit of reuse is the unit of release. Things in a component should make sense released together, with one version number. | Grouping for reusers |
| **CCP**: Common Closure | Gather things that change for the same reasons at the same times (SRP for components). | Grouping for maintainers |
| **CRP**: Common Reuse | Don't force users to depend on things they don't need (ISP for components). | Splitting |

These three are in tension. Early in a project, favor CCP (ease of change); as
other teams start reusing the code, shift toward REP and CRP.

### Coupling: how components relate

- **ADP: Acyclic Dependencies Principle.** No cycles in the component dependency
  graph. Break a cycle by applying DIP (introduce an interface in the depended-on
  side's direction) or by extracting a new component both depend on.
- **SDP: Stable Dependencies Principle.** Depend in the direction of stability.
  Instability `I = Fan-out / (Fan-in + Fan-out)`: 0 is maximally stable (many
  depend on it, it depends on nothing), 1 maximally unstable. Dependencies should
  point toward lower `I`.
- **SAP: Stable Abstractions Principle.** A component should be as abstract as it
  is stable. Abstractness `A = abstract types / total types`. Distance from the
  main sequence `D = |A + I − 1|` should be near 0.
  - **Zone of pain** (`A≈0, I≈0`): concrete and heavily depended on, so painful to
    change (e.g. a database schema). Tolerable only for things that rarely change.
  - **Zone of uselessness** (`A≈1, I≈1`): abstractions nobody uses. Delete them.

Practical takeaway: the domain/entities component is the most stable and should
contain the abstractions (ports) that volatile components implement.

## Quick review checks

- [ ] Could two different roles request changes to this class? Split by actor (SRP).
- [ ] Does adding a new variant require editing a switch in several places? (OCP/G23)
- [ ] Does any caller check the concrete type of an implementation? (LSP)
- [ ] Does a client depend on an interface where it calls only one or two methods? (ISP)
- [ ] Does policy code name a concrete DB, HTTP, or framework class? (DIP)
- [ ] Is there a cycle between packages, modules, or folders? (ADP)
- [ ] Does a stable core package import an unstable feature package? (SDP)

# Other Languages

For a language without a dedicated reference, map Martin's principles onto the
language's idioms with this checklist. If the user will work in the language
repeatedly, offer to save the result as `references/languages/<language>.md` (use
an existing file such as `go.md` as the template) and add a row to the language
table in SKILL.md.

| Concern | Decide |
| :--- | :--- |
| Module boundary | Package / module / crate / namespace / assembly per layer? |
| Visibility | How to make inner details non-public so the compiler enforces boundaries |
| Port mechanism | Interface, trait, protocol, abstract class, or function type |
| Composition root | `main`, app builder, or DI container (only if idiomatic) |
| Plain data types | struct / record / data class for DTOs and value objects |
| Error idiom | Exceptions vs. result/error values; how to add context |
| Absence | Option/nullable types; how to avoid returning null |
| Naming conventions | Where the language's conventions override generic advice |
| Enforcement | Compiler module visibility, build-graph rules, or an import linter |
| Format / lint | The standard formatter and linter |
| Test doubles | Hand-written fakes implementing ports |

Quick mappings:

- **Swift:** SwiftPM targets per layer (`Domain`, `Application`, `Adapters`, app
  target as composition root); protocols as ports; `struct` value objects; `throws`
  with typed errors; SwiftLint + swift-format.
- **Dart/Flutter:** packages or folders `domain/`, `application/`, `data/`
  (repositories), `presentation/`; abstract classes as ports; composition root in
  `main.dart` (get_it or Riverpod providers only there); enforce with
  `import_lint` or package boundaries; `dart format` + `flutter_lints`.
- **PHP:** namespaces per layer under `src/`; interfaces as ports; the framework's
  container (Symfony/Laravel) as composition root, configured outside the domain;
  **Deptrac** for layer rules; PHP-CS-Fixer + PHPStan.
- **Ruby/Rails:** plain Ruby objects in `app/domain` and `app/use_cases`;
  ActiveRecord models as persistence adapters; duck-typed ports documented by
  fakes in tests; **Packwerk** for boundaries; RuboCop. As with Django, recommend
  against full layering for CRUD-heavy apps.
- **Elixir:** contexts as the boundary; behaviours as ports; configuration-injected
  adapters; `boundary` library for enforcement.

The bundled `scripts/check_boundaries.py` supports TS/JS and Python only; for other
languages, rely on the native enforcer.

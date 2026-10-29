# Go

Applies to HTTP/gRPC services, workers, and CLIs.

Go fits Clean Architecture naturally: interfaces are satisfied implicitly, so **the
consumer declares the interface it needs** (a port), and the adapter never imports
it. That is dependency inversion with no ceremony.

## Layout

```text
cmd/
└─ orderd/main.go              composition root: config, adapters, wiring, start server
internal/
├─ order/                      one package per feature ("screaming")
│  ├─ order.go                 entity + value objects + domain errors (package order)
│  ├─ service.go               use cases + the port interfaces they consume
│  └─ service_test.go          tests with in-memory fakes
├─ postgres/                   adapter: implements order.Repository with pgx/sql
├─ stripe/                     adapter: implements order.PaymentGateway
└─ httpapi/                    adapter: handlers, request/response JSON, presenters
```

`internal/` makes packages unimportable from outside the module. Avoid generic
package names (`util`, `common`, `models`, `types`): a package name is part of
every identifier it exports (`order.Service`, not `services.OrderService`).

For larger systems, split `order` into `order` (entities) and `order/app` (use
cases) only when it grows; Go favors fewer, cohesive packages.

## Ports, use cases, composition root

```go
// internal/order/service.go
type Repository interface {
	Get(ctx context.Context, id ID) (Order, error)
	Save(ctx context.Context, o Order) error
}

type Clock interface{ Now() time.Time }

type Service struct {
	repo  Repository
	clock Clock
}

func NewService(repo Repository, clock Clock) *Service {
	return &Service{repo: repo, clock: clock}
}

func (s *Service) Place(ctx context.Context, req PlaceRequest) (ID, error) {
	o, err := New(req.CustomerID, req.Lines, s.clock.Now()) // order.New validates rules
	if err != nil {
		return "", err
	}
	if err := s.repo.Save(ctx, o); err != nil {
		return "", fmt.Errorf("saving order %s: %w", o.ID, err)
	}
	return o.ID, nil
}

// cmd/orderd/main.go
func main() {
	cfg := mustLoadConfig()
	db := mustOpenDB(cfg.DatabaseURL)
	svc := order.NewService(postgres.NewOrderRepository(db), realClock{})
	log.Fatal(http.ListenAndServe(cfg.Addr, httpapi.NewHandler(svc)))
}
```

- **Accept interfaces, return structs.** Constructors return concrete types;
  parameters take the smallest interface needed (ISP falls out naturally).
- Keep interfaces small (one to three methods) and defined where they're used, not
  next to the implementation.
- Manual wiring in `main` is idiomatic. Use `google/wire` (code generation) only
  if wiring gets unwieldy.
- `context.Context` is standard library and fine to pass through use cases. Don't
  stash dependencies in it.

## Clean Code idioms in Go

- **Names:** short, clear names for small scopes (`i`, `r`, `ctx`), longer for
  wider scopes (N5). Exported `MixedCaps`; no `Get` prefix on getters
  (`o.Total()`). Single-method interfaces are named method + `er` (`Saver`).
  Don't stutter: `order.Order` is fine, `order.OrderService` is not.
- **Errors are values, not exceptions.** Return `error` as the last result; wrap
  with context using `fmt.Errorf("...: %w", err)`; check with `errors.Is` and
  `errors.As`. Define domain errors as sentinel values or types in the domain
  package (`var ErrOutOfStock = errors.New(...)`). Map them to HTTP status in the
  adapter. Don't `panic` for expected failures. Handle each error once: log it
  *or* return it, not both.
- **Functions:** guard clauses and early returns keep the happy path at minimum
  indentation; this is Go's version of "one level of abstraction".
- **Zero values:** design types so the zero value is useful where possible.
  Return empty slices, not nil, when callers will range or serialize them.
- **Flag arguments:** use separate functions or functional options
  (`WithTimeout(d)`) instead of booleans (F3).
- **Comments:** doc comments on every exported identifier, starting with its name.
  This is where Go's culture and Martin's "public API docs are good comments"
  agree.

## Rules of thumb

- Feature/domain packages import only the standard library and other domain
  packages. No `database/sql` drivers, `net/http`, `pgx`, AWS SDK, or `os.Getenv`.
- Adapters import the domain package; the domain never imports adapters.
- Only `cmd/*/main.go` imports every package.

## Enforcement

- `internal/` visibility and the compiler's ban on import cycles (ADP enforced for
  free).
- **depguard** (via golangci-lint): deny lists per path, e.g. forbid
  `**/internal/postgres` and `net/http` in `**/internal/order/**`.
- **go-arch-lint** (`.go-arch-lint.yml`): declare components and allowed
  dependencies.
- Formatting and lint: `gofmt`/`goimports`, `go vet`, golangci-lint (staticcheck,
  revive, errcheck).

## Testing

- `go test` with **table-driven tests** for entities and use cases; fakes are small
  structs implementing the port interfaces in the `_test.go` file.
- Adapters: integration tests against testcontainers-go or a local DB, behind a
  build tag (`//go:build integration`) or `testing.Short()`.
- HTTP: `httptest.NewRecorder` / `httptest.NewServer` with a service built from
  fakes.

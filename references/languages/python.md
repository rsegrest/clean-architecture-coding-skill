# Python

Applies to FastAPI, Django, Flask, CLIs, workers, and data/ML services.

## Layout

```text
src/<app>/
├─ orders/                     one package per feature ("screaming"); or layer-first if small
│  ├─ domain/
│  │  ├─ order.py              @dataclass(frozen=True) / plain classes, pure methods
│  │  ├─ money.py              value objects
│  │  └─ errors.py             domain exceptions
│  ├─ application/
│  │  ├─ ports.py              typing.Protocol interfaces
│  │  ├─ dto.py                request/response dataclasses
│  │  └─ place_order.py        one use case per module
│  └─ adapters/
│     ├─ sql_order_repository.py   (SQLAlchemy / Django ORM here only)
│     ├─ stripe_gateway.py
│     └─ api.py                FastAPI router / Django views / Click commands + presenters
└─ main.py                     composition root
tests/
├─ unit/                       domain + use cases with fakes (no DB, no network)
└─ integration/                adapters against real/containerized services
```

Use a `src/` layout with `pyproject.toml` so imports are absolute
(`from app.orders.domain...`).

## Ports, use cases, composition root

```python
# application/ports.py
class OrderRepository(Protocol):
    def get(self, order_id: OrderId) -> Order: ...
    def save(self, order: Order) -> None: ...

# application/place_order.py
@dataclass(frozen=True)
class PlaceOrder:
    orders: OrderRepository
    clock: Clock

    def __call__(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        order = Order.place(request.customer_id, request.lines, self.clock.now())
        self.orders.save(order)
        return PlaceOrderResponse(order_id=order.id)

# main.py: the only module importing concrete adapters
def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.db_url)
    return Container(place_order=PlaceOrder(SqlOrderRepository(engine), SystemClock()))
```

- `typing.Protocol` (structural) keeps adapters from importing the port; use
  `abc.ABC` if you want explicit registration.
- **FastAPI:** expose the container through `Depends(get_container)`; routers call
  use cases and map results through presenters into Pydantic response models.
  **Pydantic models live in adapters, not in domain.**
- **Django:** Clean Architecture fights Django's "fat model" default. Keep models
  as persistence adapters, put rules in `domain/` and `application/`, and map in
  repositories. If the app is mostly CRUD, recommend not doing this.

## Clean Code idioms in Python

- **Names:** PEP 8: `snake_case` functions/variables, `PascalCase` classes,
  `UPPER_SNAKE` constants, `_leading_underscore` for module-private. Avoid vague
  module names like `utils.py` and `helpers.py`; name by concept.
- **Value objects:** `@dataclass(frozen=True, slots=True)` with validation in
  `__post_init__` or a classmethod factory. Use `NewType` for IDs.
- **Arguments:** use keyword-only parameters (`def f(*, dry_run: bool)`) when a
  boolean is unavoidable; better, split the function (F3). Group long parameter
  lists into a dataclass (F1).
- **Type switches:** `match` on a closed set of types is acceptable once; if it
  repeats, use polymorphism or `functools.singledispatch` (G23).
- **Errors:** raise domain exceptions subclassing one base `AppError`, with
  context. `raise ... from err` when wrapping. Never use bare `except:`; catch at
  the entrypoint and map to HTTP or exit codes.
- **None:** return empty collections, not `None`. Use `Optional[...]` /
  `X | None` only where absence is a real outcome, and type-check it (mypy or
  pyright in strict mode).
- **Comments:** docstrings for public functions and classes; avoid restating type
  hints in prose.
- Prefer pure functions in the domain; keep module-level state and import-time
  side effects out of inner layers.

## Rules of thumb

- `domain/` and `application/` import only the standard library (and each other,
  inward). No `sqlalchemy`, `django`, `fastapi`, `pydantic`, `requests`, `httpx`,
  `boto3`, `os.environ`, `open()`, or `print()`.
- Inject time and randomness (`Clock`, `IdGenerator` ports) when rules depend on
  them.
- Settings are read in `main.py` (e.g. pydantic-settings there) and passed down.

## Enforcement

**import-linter** (`pip install import-linter`, run `lint-imports`):

```toml
[tool.importlinter]
root_package = "app"

[[tool.importlinter.contracts]]
name = "Clean Architecture layers"
type = "layers"
layers = ["app.orders.adapters", "app.orders.application", "app.orders.domain"]

[[tool.importlinter.contracts]]
name = "Inner layers are framework-free"
type = "forbidden"
source_modules = ["app.orders.domain", "app.orders.application"]
forbidden_modules = ["sqlalchemy", "django", "fastapi", "pydantic", "requests", "httpx"]
```

(`main.py` is outside the layer list, so it may import everything.) The bundled
`scripts/check_boundaries.py` also covers Python. Formatting and lint: ruff
(format + lint) and mypy or pyright.

## Testing

- Unit: pytest with hand-written fakes implementing the Protocols. Prefer fakes to
  `unittest.mock`; they double as port documentation.
- Integration: adapters against testcontainers, SQLite, or respx.
- E2E: FastAPI `TestClient` / Django test client with a test container.

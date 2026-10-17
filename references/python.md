# Python

## Layout

```text
src/<app>/
├─ domain/
│  ├─ entities.py          @dataclass(frozen=True) / plain classes, pure methods
│  ├─ value_objects.py
│  └─ errors.py            domain exceptions
├─ application/
│  ├─ ports.py             typing.Protocol (or abc.ABC) interfaces
│  ├─ dto.py               dataclasses / pydantic-free plain types
│  └─ use_cases/           get_board.py, add_comment.py
├─ adapters/
│  ├─ repositories/        sql_board_repository.py (SQLAlchemy/Django ORM here only)
│  ├─ gateways/            http clients, S3, email, LLM APIs
│  └─ presenters/          domain → API schema / CLI output
├─ entrypoints/            (framework layer)
│  ├─ api/                 FastAPI routers / Django views / Flask blueprints
│  ├─ cli/                 Typer/Click commands
│  └─ workers/
└─ main.py                 composition root (build adapters, inject into use cases)
tests/
├─ unit/                   domain + use cases with fakes (no DB, no network)
└─ integration/            adapters against real/containerized services
```

Use a `src/` layout with `pyproject.toml` so imports are absolute (`from app.domain...`).

## Patterns

```python
# application/ports.py
class BoardRepository(Protocol):
    def get(self, board_id: str) -> Board: ...

# application/use_cases/get_board.py
@dataclass
class GetBoard:
    repo: BoardRepository
    def __call__(self, board_id: str) -> Board:
        return self.repo.get(board_id)

# main.py — the only module importing concrete adapters
def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.db_url)
    return Container(get_board=GetBoard(SqlBoardRepository(engine)))
```

FastAPI: expose the container through a dependency (`Depends(get_container)`),
routers call use cases and map results with presenters into Pydantic response
models. **Pydantic models live in `entrypoints/` (or adapters), not in `domain/`.**

Django: Clean Architecture fights Django's "fat model" default. For Django, keep
models as persistence adapters, put rules in `domain/` and `application/`, and map
between them in repositories. If the app is mostly CRUD, recommend not doing this.

Rules of thumb:
- `domain/` and `application/` import only the standard library (and each other
  inward). No `sqlalchemy`, `django`, `fastapi`, `pydantic`, `requests`, `httpx`,
  `boto3`, `os.environ`.
- Inject time and randomness (`Clock`, `IdGenerator` ports) when rules depend on them.
- Settings are read in `main.py` and passed down; never read env vars in inner layers.

## Enforcement

**import-linter** (`pip install import-linter`, run `lint-imports`):

```toml
[tool.importlinter]
root_package = "app"

[[tool.importlinter.contracts]]
name = "Clean Architecture layers"
type = "layers"
layers = ["app.entrypoints", "app.adapters", "app.application", "app.domain"]

[[tool.importlinter.contracts]]
name = "Inner layers are framework-free"
type = "forbidden"
source_modules = ["app.domain", "app.application"]
forbidden_modules = ["sqlalchemy", "django", "fastapi", "pydantic", "requests", "httpx"]
```

(`main.py` is outside the layer list, so it may import everything.)

## Testing

- Unit: pytest with hand-written fakes implementing the Protocols (prefer fakes to
  `unittest.mock`; they double as port documentation).
- Integration: adapters against testcontainers/SQLite/respx.
- E2E: FastAPI `TestClient` with a test container.

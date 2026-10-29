# Rust

Applies to services (axum, actix-web), CLIs, and libraries. Martin's *Functional
Design* is a useful companion here: immutable data, pure functions, and
traits-as-interfaces map directly onto SOLID.

## Layout: Cargo workspace, one crate per layer

```text
Cargo.toml                     [workspace] members = ["crates/*", "apps/*"]
crates/
├─ domain/                     entities, value objects, domain errors — no deps (maybe thiserror)
├─ application/                use cases + port traits → domain
├─ adapters-postgres/          sqlx repositories → application, domain
└─ adapters-http/              axum routes, DTOs (serde), presenters → application
apps/
└─ orderd/src/main.rs          composition root: config, adapters, wiring, server start
```

A crate can only use crates in its `[dependencies]`, so the crate graph enforces
the dependency rule, and Cargo forbids cycles between crates (ADP). For a smaller
app, use modules in one crate (`mod domain; mod application; mod adapters;`) with
`pub(crate)` visibility, and accept weaker enforcement.

## Ports, use cases, composition root

```rust
// crates/application/src/ports.rs
pub trait OrderRepository: Send + Sync {
    async fn find(&self, id: OrderId) -> Result<Option<Order>, RepoError>;
    async fn save(&self, order: &Order) -> Result<(), RepoError>;
}

pub trait Clock: Send + Sync {
    fn now(&self) -> DateTime;
}

// crates/application/src/place_order.rs: generic, so no dyn and no boxing
pub struct PlaceOrder<R: OrderRepository, C: Clock> {
    orders: R,
    clock: C,
}

impl<R: OrderRepository, C: Clock> PlaceOrder<R, C> {
    pub fn new(orders: R, clock: C) -> Self { Self { orders, clock } }

    pub async fn execute(&self, cmd: PlaceOrderCommand) -> Result<OrderId, PlaceOrderError> {
        let order = Order::place(cmd.customer_id, cmd.lines, self.clock.now())?;
        self.orders.save(&order).await?;
        Ok(order.id())
    }
}

// apps/orderd/src/main.rs
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::from_env()?;
    let pool = PgPool::connect(&config.database_url).await?;
    let place_order = PlaceOrder::new(PgOrderRepository::new(pool), SystemClock);
    adapters_http::serve(Arc::new(place_order), config.addr).await
}
```

- **Generics vs. `dyn Trait`:** generics give static dispatch and work with native
  `async fn` in traits (Rust 1.75+). Two caveats: a public trait's `async fn` can't
  promise its future is `Send` (needed for `tokio::spawn` and most web servers), so
  declare `fn save(..) -> impl Future<Output = ..> + Send` or use the
  `trait-variant` crate; and native async trait methods are not object-safe. If
  you need `Arc<dyn OrderRepository>` (runtime choice of adapter, fewer type
  parameters), use the `async-trait` crate. All of these satisfy the dependency
  rule.
- Ports take and return domain types; adapters convert from `sqlx::Row` or serde
  DTOs.

## Clean Code idioms

- **Names:** `snake_case` functions/modules, `PascalCase` types/traits,
  `SCREAMING_SNAKE` consts. Conversion methods follow `as_` / `to_` / `into_`
  conventions; constructors are `new` or `try_new` / `parse`.
- **Value objects:** newtypes (`struct OrderId(Uuid)`) with private fields and
  validating constructors. *Parse, don't validate*: once a `Quantity` exists it is
  valid, so no re-checking downstream.
- **Errors:** `Result` everywhere. Use `thiserror` for typed errors in
  `domain`/`application`/adapters (define them by how callers handle them, ch. 7),
  and `anyhow` only in the binary or tests. Add context when propagating. No
  `unwrap()`/`expect()` in non-test code except for true invariants, with a message
  saying why.
- **No null:** `Option<T>` for absence; return empty `Vec`s rather than
  `Option<Vec<_>>` unless "unknown" differs from "none".
- **Closed variants:** `enum` + exhaustive `match` is idiomatic; for open sets
  (plugins), use traits (OCP).
- **Flag arguments:** replace `bool` parameters with a two-variant enum or
  separate functions (F3).
- **Comments:** `///` doc comments with examples on public items (doctests make
  them executable); `//` for *why*, not *what*.
- Keep `unsafe` out of domain and application crates (`#![forbid(unsafe_code)]`).

## Enforcement

- Workspace crate graph (primary). Domain crate's `Cargo.toml` lists no I/O or
  framework crates.
- **cargo-deny** `[bans]` with `wrappers` restricts which crates may depend on a
  given crate (e.g. only `adapters-postgres` may use `sqlx`).
- `#![forbid(unsafe_code)]` and `#![deny(clippy::unwrap_used)]` in inner crates.
- Formatting and lint: `rustfmt`, `cargo clippy -- -D warnings` (consider
  `clippy::pedantic` selectively).

## Testing

- Unit tests in `#[cfg(test)] mod tests` inside domain/application crates with
  hand-written fakes (`struct InMemoryOrders(Mutex<HashMap<..>>)`). `mockall` only
  for interaction checks.
- Adapter integration tests in `tests/` using testcontainers or `#[sqlx::test]`.
- HTTP: call the axum `Router` directly with `tower::ServiceExt::oneshot`.
- Property tests (proptest) suit value-object invariants.

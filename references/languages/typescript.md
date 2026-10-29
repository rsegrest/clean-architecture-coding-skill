# TypeScript / JavaScript

Applies to Node, Deno, Bun, libraries, CLIs, and backends (Express, Fastify, Hono,
NestJS). For React, React Native, or Next.js, read this file first, then
[react.md](./react.md).

## Layout: single package (default)

```text
src/
├─ orders/                       one folder per feature/bounded context ("screaming")
│  ├─ domain/                    Order.ts, Money.ts, errors.ts   (pure, no imports outward)
│  ├─ application/
│  │  ├─ ports/                  OrderRepository.ts, PaymentGateway.ts, Clock.ts
│  │  └─ useCases/               PlaceOrder.ts, CancelOrder.ts
│  ├─ adapters/
│  │  ├─ persistence/            PgOrderRepository.ts         (pg/Prisma/Drizzle here only)
│  │  ├─ payments/               StripePaymentGateway.ts
│  │  └─ http/                   orderRoutes.ts, OrderPresenter.ts (framework handlers + mapping)
│  └─ index.ts                   exports the feature's public surface only
├─ shared/                       cross-feature domain types (keep it small)
└─ main.ts                       composition root: read config, build adapters, start server
test/                            or colocated *.test.ts
```

A layer-first layout (`src/{domain,application,adapters,infrastructure}`) is fine
for small apps; feature-first scales better.

## Layout: monorepo (multiple deployables or clients)

`packages/domain` (zero runtime deps), `packages/application`, `packages/adapters`,
and one package per app (`apps/api`, `apps/worker`, `apps/web`), each with its own
composition root. Use npm/pnpm/yarn workspaces and **TypeScript project
references** (`composite: true`, `references: [...]`). A package can't import what
it doesn't list as a dependency, so the build enforces the dependency rule.

## Ports, use cases, composition root

```ts
// orders/application/ports/OrderRepository.ts
export interface OrderRepository {
  findById(id: OrderId): Promise<Order | undefined>;
  save(order: Order): Promise<void>;
}

// orders/application/useCases/PlaceOrder.ts
export class PlaceOrder {
  constructor(
    private readonly orders: OrderRepository,
    private readonly payments: PaymentGateway,
    private readonly clock: Clock,
  ) {}

  async execute(request: PlaceOrderRequest): Promise<PlaceOrderResponse> {
    const order = Order.place(request.customerId, request.lines, this.clock.now());
    await this.payments.charge(order.total());
    await this.orders.save(order);
    return { orderId: order.id };
  }
}

// main.ts — the only module that imports concrete adapters
const config = loadConfig(process.env);
const db = new Pool({ connectionString: config.databaseUrl });
const placeOrder = new PlaceOrder(new PgOrderRepository(db), new StripePaymentGateway(config.stripeKey), systemClock);
startServer({ placeOrder }, config.port);
```

- Interfaces or function types both work as ports. A single-method port can be a
  type alias: `type Clock = { now(): Date }`.
- Plain constructor injection is enough. Use a DI container (tsyringe, InversifyJS,
  NestJS modules) only if the framework already requires it, and keep container
  decorators out of `domain/` and `application/`.
- **NestJS:** treat Nest modules, controllers, and `@Injectable` providers as the
  framework/adapter layer. Use cases are plain classes registered with
  `useFactory`; bind ports with injection tokens.

## Clean Code idioms in TypeScript

- **Names:** `PascalCase` types/classes, `camelCase` functions/values,
  `UPPER_SNAKE` for true constants. No `I` prefix on interfaces (TS convention).
  Booleans read as predicates: `isPaid`, `hasItems`.
- **Value objects:** use `readonly` fields, private constructors, and static
  factories that validate (`Money.of(amount, currency)`). Use branded types for
  IDs (`type OrderId = string & { readonly __brand: "OrderId" }`) to stop mixing
  them up.
- **Avoid flag arguments and long parameter lists:** use an options object with a
  named type (F1, F3).
- **Replace type switches** with discriminated unions plus exhaustive `switch`
  (`never` check), or with polymorphism when behavior varies by type (G23).
- **Errors:** throw subclasses of a domain `Error` with context; catch at the
  delivery layer and map to HTTP status or exit code. If the codebase uses
  `Result` types (e.g. neverthrow), stay consistent; don't mix both styles in one
  layer. Never throw strings.
- **Null:** enable `strict`; return `undefined` only where "absent" is a real
  outcome and say so in the type. Prefer empty arrays over `undefined` for lists.
- **Immutability:** `readonly` arrays and properties in domain types; return new
  objects from domain operations where practical (*Functional Design*).
- Avoid `any`; use `unknown` at boundaries and parse into domain types (e.g. zod
  schemas live in adapters, not the domain).

## Rules of thumb

- `domain/` and `application/` must not import frameworks (`express`, `fastify`,
  `@nestjs/*`, `react`), I/O libraries (`pg`, `prisma`, `axios`, AWS SDK), or use
  `fetch`, `process.env`, `fs`, `Date.now()`, or `Math.random()` directly. Inject
  `Clock`/`IdGenerator` ports.
- Config is read once in `main.ts` and passed down as typed values.
- Each feature exposes a narrow `index.ts`; other features import only that.

## Enforcement

Pick one and run it in CI:

- **dependency-cruiser:** `forbidden` rules, e.g.
  `{ name: "inward-only", from: { path: "(domain|application)/" }, to: { path: "(adapters|main)" } }`
  plus `no-circular`.
- **eslint-plugin-boundaries:** element types per folder with `allow` rules.
- **ESLint `no-restricted-imports`:** in `**/domain/**` and `**/application/**`,
  ban framework packages and `**/adapters/**`.
- **Nx `enforce-module-boundaries`** with tags, for Nx monorepos.
- Project references (monorepo) enforce it at build time.
- The bundled `scripts/check_boundaries.py` also covers TS/JS.

Formatting and lint: Prettier (or Biome) + typescript-eslint with `strict`
type-checked configs.

## Testing

- Vitest, Jest, or `node:test`. Domain and use-case tests import nothing from
  adapters; use hand-written in-memory fakes:
  `class InMemoryOrderRepository implements OrderRepository { ... }`.
- Adapters: integration tests with Testcontainers or a local DB; HTTP clients
  against MSW or a stub server.
- HTTP layer: supertest / `app.inject()` with a test composition root.

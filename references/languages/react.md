# React / React Native / Next.js add-on

Read [typescript.md](./typescript.md) first. This file covers only what changes
when the delivery mechanism is React. In Clean Architecture terms, React is a
**detail**: the outermost circle. Components are Humble Objects that render view
models.

## Layout: single app

```text
src/
├─ domain/             entities, value objects, pure rules
├─ application/
│  ├─ ports/           BoardRepository.ts (interfaces only)
│  └─ useCases/        GetBoard.ts, AddComment.ts
├─ adapters/
│  ├─ infrastructure/  Http.ts, Storage.ts         (wrap fetch/axios/localStorage)
│  ├─ repositories/    HttpBoardRepository.ts      (implements ports)
│  └─ presenters/      BoardPresenter.ts           (domain → view model)
└─ ui/                 (framework layer)
   ├─ components/      dumb: props in, JSX out
   ├─ hooks/           useBoard.ts                 (thin: call use case, hold state)
   ├─ vm/              view-model types
   ├─ state/           Zustand/Redux/TanStack Query
   └─ di/              container.ts, DIProvider.tsx (composition root)
```

Feature-first (`features/board/{domain,application,adapters,ui}`) is fine; the
dependency rule matters, not the folder names.

## Layout: monorepo (web + React Native)

`packages/domain`, `packages/adapters` shared by `apps/web` and `apps/mobile`; each
app owns its `di/` and UI. Platform-specific adapters (AsyncStorage vs.
localStorage) implement the same port.

## Patterns

**Composition root exposed through context**

```ts
// ui/di/container.ts — the ONLY file importing concrete adapters
const http = new Http(import.meta.env.VITE_API_URL);
export const container = {
  getBoard: new GetBoard(new HttpBoardRepository(http)),
};
export type Container = typeof container;
// DIProvider.tsx puts `container` in React context; useDI() reads it.
```

**Hook as thin glue**

```ts
export function useBoard(id: string) {
  const { getBoard } = useDI();
  return useQuery({
    queryKey: ["board", id],
    queryFn: () => getBoard.execute(id).then(BoardPresenter.toViewModel),
  });
}
```

**Humble component**

```tsx
export function BoardView({ board }: { board: BoardViewModel }) {
  return <h1 className={board.isOverdue ? "overdue" : undefined}>{board.title}</h1>;
}
```

The presenter computed `isOverdue` and formatted strings; the component only
displays them.

## Clean Code in React

- A component does one thing. Split when JSX mixes levels of abstraction (layout +
  formatting + data loading).
- Name event handler props `onX` and handler functions `handleX`; name components
  for what they show (`InvoiceSummary`), not how (`BlueBox`).
- No boolean-flag props that switch whole render branches (F3). Make two
  components or use composition (`children`, slots).
- Custom hooks extract stateful logic; they contain no business rules.
- Avoid prop drilling beyond 2–3 levels; use composition or context.

## Rules of thumb

- Components receive view models; they never import from `adapters/` or call
  `fetch`.
- Data-fetching libraries (TanStack Query/SWR) live in `ui/`, wrapping use cases.
- `domain/` and `application/` never import `react`, state libraries, `window`,
  `localStorage`, or `import.meta.env`.
- **Next.js:** server components, route handlers, and server actions are the
  framework layer. They call use cases through a server-side container
  (`server/container.ts`, guarded with `import "server-only"`). Keep `"use server"`
  functions thin.

## Enforcement and testing

- Same tools as typescript.md; add `react`, `react-dom`, `react-native`, `next`,
  and state libraries to the banned list for inner layers.
- UI tests: React Testing Library rendering with a test container passed to
  `DIProvider`. Presenters get plain unit tests.
- Adapter tests: MSW for HTTP.

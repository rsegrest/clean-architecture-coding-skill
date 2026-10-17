# TypeScript / React

## Layout: single package (default)

```text
src/
├─ domain/
│  ├─ entities/        Board.ts, Comment.ts          (classes or types + pure fns)
│  ├─ aggregates/      BoardAggregate.ts
│  └─ dto/             BoardDTO.ts                   (plain serializable shapes)
├─ application/        (a.k.a. useCases)
│  ├─ ports/           BoardRepository.ts            (interfaces only)
│  └─ useCases/        GetBoard.ts, AddComment.ts
├─ adapters/
│  ├─ infrastructures/ Http.ts, Storage.ts           (wrap fetch/axios/localStorage)
│  ├─ repositories/    HttpBoardRepository.ts        (implements ports)
│  └─ presenters/      BoardPresenter.ts             (domain → view model)
└─ ui/                 (framework layer)
   ├─ components/
   ├─ hooks/           useBoard.ts                   (thin: call use case, hold state)
   ├─ vm/              view-model types for components
   ├─ state/           Zustand/Redux/Recoil/Query stores
   └─ di/              container.ts, DIProvider.tsx  (composition root)
```

## Layout: monorepo (multiple clients, e.g. web + React Native)

Mirror falsy/react-with-clean-architecture: `packages/domain`, `packages/adapter`,
`packages/web`, `packages/mobile`. `domain` has zero deps; `adapter` depends on
`domain`; each client depends on both and owns its own `di/`. Use npm/yarn/pnpm
workspaces. Package boundaries enforce the rule for free.

## Patterns

**Port + use case**

```ts
// application/ports/BoardRepository.ts
export interface BoardRepository {
  getBoard(id: string): Promise<BoardDTO>;
}

// application/useCases/GetBoard.ts
export class GetBoard {
  constructor(private readonly repo: BoardRepository) {}
  async execute(id: string): Promise<Board> {
    return Board.fromDTO(await this.repo.getBoard(id)); // domain rules live in Board
  }
}
```

**Composition root + React context**

```ts
// ui/di/container.ts — the ONLY file importing concrete adapters
const http = new Http(import.meta.env.VITE_API_URL);
export const container = {
  getBoard: new GetBoard(new HttpBoardRepository(http)),
};
export type Container = typeof container;
// DIProvider.tsx exposes `container` via React context; useDI() reads it.
```

**Hook as thin glue**

```ts
export function useBoard(id: string) {
  const { getBoard } = useDI();
  return useQuery({ queryKey: ["board", id], queryFn: () => getBoard.execute(id).then(BoardPresenter.toVM) });
}
```

Rules of thumb:
- Components receive view models; they never import from `adapters/` or call `fetch`.
- Hooks may call use cases and state libraries; they contain no business rules.
- Domain/application must not import `react`, state libs, `axios`, `fetch`,
  `window`, `localStorage`, or `import.meta.env`.
- Data-fetching libraries (React Query/SWR) belong in `ui/`, wrapping use cases.
- Next.js server components/actions are the framework layer; call use cases from
  them via a server-side container.

## Enforcement

Pick one and add to CI:

- **eslint-plugin-boundaries** — element types per folder, `allow` rules per layer.
- **dependency-cruiser** — `forbidden` rules, e.g.
  `{ from: { path: "^src/(domain|application)" }, to: { path: "^src/(adapters|ui)" } }`.
- `no-restricted-imports` in `src/domain/**` and `src/application/**` banning
  `react`, `axios`, and `**/adapters/**`, `**/ui/**`.
- TS path aliases (`@domain/*`, `@application/*`) make violations easy to grep.

## Testing

- Domain: plain unit tests (Vitest/Jest), no mocks needed.
- Use cases: inject an in-memory fake implementing the port.
- Adapters: test against MSW or a test server.
- UI: React Testing Library with a test container passed to `DIProvider`.

# C# / .NET

Applies to ASP.NET Core (Minimal APIs or MVC), worker services, Blazor, and MAUI.

## Layout: one project per layer

```text
src/
├─ Orders.Domain/              entities, value objects, domain exceptions — no package references
├─ Orders.Application/         use cases, port interfaces, request/response records → Domain
├─ Orders.Infrastructure/      EF Core DbContext, repositories, HTTP clients → Application
└─ Orders.Api/                 ASP.NET Core endpoints, presenters, Program.cs → Application, Infrastructure
tests/
├─ Orders.Domain.Tests/
├─ Orders.Application.Tests/
└─ Orders.Api.IntegrationTests/
```

Project references enforce the dependency rule at compile time: `Domain` can't
reference `Infrastructure` without someone editing the `.csproj`. Within each
project, organize folders by feature (`Orders/PlaceOrder/`) so it screams the
domain. Mark types `internal` unless another project needs them.

## Ports, use cases, composition root

```csharp
// Orders.Application
public interface IOrderRepository
{
    Task<Order?> FindAsync(OrderId id, CancellationToken ct);
    Task SaveAsync(Order order, CancellationToken ct);
}

public sealed class PlaceOrder(IOrderRepository orders, TimeProvider clock)
{
    public async Task<OrderId> ExecuteAsync(PlaceOrderCommand command, CancellationToken ct)
    {
        var order = Order.Place(command.CustomerId, command.Lines, clock.GetUtcNow());
        await orders.SaveAsync(order, ct);
        return order.Id;
    }
}

// Orders.Api/Program.cs: the composition root
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddDbContext<OrdersDbContext>(o => o.UseNpgsql(builder.Configuration.GetConnectionString("Orders")));
builder.Services.AddScoped<IOrderRepository, EfOrderRepository>();
builder.Services.AddSingleton(TimeProvider.System);   // built-in clock port (.NET 8+)
builder.Services.AddScoped<PlaceOrder>();
var app = builder.Build();
app.MapPost("/orders", async (PlaceOrderRequest req, PlaceOrder placeOrder, CancellationToken ct) =>
    Results.Created($"/orders/{await placeOrder.ExecuteAsync(req.ToCommand(), ct)}", null));
app.Run();
```

- `Microsoft.Extensions.DependencyInjection` is the container; registration
  belongs to the composition root. `AddInfrastructure(this IServiceCollection)`
  extension methods in the Infrastructure project are a common, acceptable way to
  group registrations; `Program.cs` still calls them.
- **EF Core:** keep attributes out of domain entities. Configure the mapping with
  `IEntityTypeConfiguration<T>` in Infrastructure. Mapping domain entities
  directly with the Fluent API is a pragmatic partial boundary; separate
  persistence models are a full one. Don't leak `IQueryable` or `DbContext`
  through ports.
- A mediator library is optional. Plain use-case classes injected into endpoints
  are simpler and satisfy the architecture.

## Clean Code idioms

- **Names:** .NET conventions: `PascalCase` types, methods, and properties;
  `camelCase` locals and parameters; `_camelCase` private fields. Interfaces take
  the `I` prefix by convention; this is the language idiom, so keep it despite
  *Clean Code*'s "no encodings". Async methods end in `Async`.
- **Value objects:** `record` / `readonly record struct` with validation in a
  static factory; strongly typed IDs (`readonly record struct OrderId(Guid Value)`).
- **Closed variants:** switch expressions with pattern matching are fine once; when
  the same switch repeats, use polymorphism (G23).
- **Errors:** exceptions for exceptional cases, with a domain exception hierarchy
  carrying context. Map to `ProblemDetails` in an exception handler
  (`IExceptionHandler`). If the codebase uses a Result type for expected outcomes,
  stay consistent within a layer.
- **Null:** enable `<Nullable>enable</Nullable>` and treat warnings as errors;
  return empty collections, not null.
- **Async:** pass `CancellationToken` through use cases; never `.Result` or
  `.Wait()`.
- Keep `Program.cs` declarative; move endpoint groups into `MapOrders()` extension
  methods per feature.

## Enforcement

- Project references (primary enforcement).
- **NetArchTest.Rules** or **ArchUnitNET** tests:

```csharp
[Fact]
public void Domain_and_application_do_not_depend_on_infrastructure_or_frameworks()
{
    var result = Types.InAssemblies([typeof(Order).Assembly, typeof(PlaceOrder).Assembly])
        .ShouldNot()
        .HaveDependencyOnAny("Orders.Infrastructure", "Orders.Api",
                             "Microsoft.EntityFrameworkCore", "Microsoft.AspNetCore")
        .GetResult();
    Assert.True(result.IsSuccessful);
}
```

- `Directory.Build.props` with `TreatWarningsAsErrors`, `Nullable`,
  `AnalysisLevel=latest-recommended`; `.editorconfig` for style; `dotnet format`
  in CI.

## Testing

- xUnit, NUnit, or MSTest. Use cases with hand-written fakes
  (`InMemoryOrderRepository`); NSubstitute or Moq only for interaction checks.
- `FakeTimeProvider` (Microsoft.Extensions.TimeProvider.Testing) for time.
- Integration: `WebApplicationFactory<Program>` with Testcontainers for the DB.

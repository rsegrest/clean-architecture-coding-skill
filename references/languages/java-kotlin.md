# Java / Kotlin (JVM)

Applies to Spring Boot, Quarkus, Micronaut, Ktor, and plain JVM services. *Clean
Code*'s examples are in Java, so the book's advice maps over directly.

## Layout: Gradle (or Maven) modules per layer

```text
settings.gradle.kts            include("domain", "application", "adapters:persistence", "adapters:web", "bootstrap")
domain/                        com.acme.orders.domain       — no dependencies
application/                   com.acme.orders.application  — depends on :domain
adapters/persistence/          JPA/jOOQ/Exposed repositories — depends on :application
adapters/web/                  controllers, DTOs, presenters  — depends on :application
bootstrap/                     @SpringBootApplication / main, config — depends on all
```

Module dependencies enforce the dependency rule at compile time. For a smaller app,
use one module with packages per feature (`com.acme.orders.{domain,application,adapters}`)
plus ArchUnit (below).

## Ports, use cases, composition root

```java
// application: port owned by the use case
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    void save(Order order);
}

public final class PlaceOrder {
    private final OrderRepository orders;
    private final Clock clock;               // java.time.Clock is a ready-made port

    public PlaceOrder(OrderRepository orders, Clock clock) {
        this.orders = orders;
        this.clock = clock;
    }

    public OrderId execute(PlaceOrderCommand command) {
        Order order = Order.place(command.customerId(), command.lines(), clock.instant());
        orders.save(order);
        return order.id();
    }
}

// bootstrap: the composition root (Spring @Configuration)
@Configuration
class OrderWiring {
    @Bean PlaceOrder placeOrder(OrderRepository orders) {
        return new PlaceOrder(orders, Clock.systemUTC());
    }
}
```

```kotlin
// Kotlin equivalent
interface OrderRepository {
    fun findById(id: OrderId): Order?
    fun save(order: Order)
}

class PlaceOrder(private val orders: OrderRepository, private val clock: Clock) {
    operator fun invoke(command: PlaceOrderCommand): OrderId =
        Order.place(command.customerId, command.lines, clock.instant())
            .also(orders::save)
            .id
}
```

- **Keep framework annotations out of `domain` and `application`:** no
  `@Entity`, `@Service`, `@Autowired`, `@Transactional`, or Jackson annotations.
  Register use cases as beans in `bootstrap` configuration classes instead.
- **JPA entities are persistence adapters,** separate from domain entities; map in
  the repository adapter. This costs a mapping layer; for pure CRUD, say so and
  consider skipping it.
- Transactions: wrap use-case calls in the adapter/bootstrap layer (a decorator,
  or `TransactionTemplate` in a web adapter), not with annotations in the core.

## Clean Code idioms

- **Names:** `PascalCase` types, `camelCase` methods/fields, `UPPER_SNAKE`
  constants. No `I` prefix or `Impl` suffix. Name the implementation for what
  makes it different (`JpaOrderRepository`).
- **Value objects:** Java `record`s and Kotlin `data class`/`@JvmInline value
  class` with validation in the compact constructor or `init`.
- **Closed variants:** sealed interfaces + `switch` pattern matching (Java 21) or
  Kotlin `when` are exhaustive; one such switch is fine. If it repeats across the
  code, move behavior into the types (G23).
- **Errors:** prefer **unchecked** exceptions (*Clean Code* ch. 7). Create a small
  domain exception hierarchy with context; translate at the web adapter
  (`@ControllerAdvice`). In Kotlin, sealed result types are idiomatic for expected
  business outcomes; exceptions for the unexpected.
- **Null:** Java: return `Optional` for "may be absent" results, never as a
  parameter or field; annotate with JSpecify `@NullMarked`. Kotlin: nullable
  types; avoid `!!`.
- **Immutability:** `final` fields, unmodifiable collections (`List.copyOf`),
  Kotlin `val` and read-only collection types.
- **Lombok** is acceptable in adapters; prefer records in the domain.

## Enforcement

- Module boundaries (Gradle/Maven) or **JPMS** `module-info.java` with explicit
  `exports`.
- **ArchUnit** tests (Java and Kotlin):

```java
@ArchTest
static final ArchRule layers = layeredArchitecture().consideringAllDependencies()
    .layer("Domain").definedBy("..domain..")
    .layer("Application").definedBy("..application..")
    .layer("Adapters").definedBy("..adapters..")
    .layer("Bootstrap").definedBy("..bootstrap..")
    .whereLayer("Bootstrap").mayNotBeAccessedByAnyLayer()
    .whereLayer("Adapters").mayOnlyBeAccessedByLayers("Bootstrap")
    .whereLayer("Application").mayOnlyBeAccessedByLayers("Adapters", "Bootstrap")
    .whereLayer("Domain").mayOnlyBeAccessedByLayers("Application", "Adapters", "Bootstrap");

@ArchTest
static final ArchRule frameworkFree = noClasses().that().resideInAnyPackage("..domain..", "..application..")
    .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "jakarta.persistence..");
```

- Kotlin-native alternative: **Konsist**.
- Formatting and lint: Spotless with google-java-format, or ktlint; Checkstyle, PMD,
  SpotBugs, or Error Prone (Java); detekt (Kotlin).

## Testing

- JUnit 5 (+ AssertJ, or Kotest for Kotlin). Use cases tested with hand-written
  in-memory repositories; Mockito/MockK only for interaction checks.
- Adapters: `@DataJpaTest` / Testcontainers for persistence; `@WebMvcTest` or
  `MockMvc` for controllers with use cases stubbed.
- `java.time.Clock.fixed(...)` for deterministic time.

# Package by Feature Architecture (Vertical Slice Architecture)

## Overview

This document describes the **Package by Feature** architectural pattern (also known as **Vertical Slice Architecture**), which organizes code by business features/domains rather than technical layers.

---

## 📚 Terminology & Patterns

### **Package by Feature** (Vertical Organization)

Also known as:
- **Vertical Slice Architecture**
- **Feature-based Organization**
- **Domain-centric Architecture**
- **Modular Monolith** (when you have multiple such modules)
- **Screaming Architecture** (Uncle Bob Martin) - where the folder structure "screams" what the app does, not what framework it uses

**Structure**:
```
app/
├── notification/          # Domain module
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── controllers/
│   ├── schemas/          # DTOs
│   └── utils/
│
├── reporting/            # Domain module
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── controllers/
│   ├── schemas/
│   └── utils/
│
└── user_management/      # Domain module
    ├── models/
    ├── repositories/
    ├── services/
    ├── controllers/
    ├── schemas/
    └── utils/
```

### **Package by Layer** (Horizontal Organization)

Traditional layered architecture:
```
app/
├── controllers/          # All controllers
├── services/             # All services
├── repositories/         # All repositories
├── models/               # All models
└── schemas/              # All DTOs
```

---

## ✅ Advantages of Package by Feature

| Advantage | Description |
|-----------|-------------|
| **High Cohesion** | Related code is co-located; everything for a feature is in one place |
| **Low Coupling** | Features are isolated; changes in one feature don't affect others |
| **Easier Navigation** | Developers can find all code for a feature in one directory |
| **Team Ownership** | Teams can own entire features/domains |
| **Microservice Ready** | Each module can potentially become a microservice |
| **Bounded Contexts** | Aligns with DDD bounded contexts |
| **Screaming Architecture** | Folder structure shows business capabilities, not technical layers |
| **Easier Deletion** | Can delete an entire feature by removing one directory |
| **Reduced Merge Conflicts** | Different teams work in different directories |

---

## ❌ Disadvantages

| Disadvantage | Description |
|--------------|-------------|
| **Code Duplication** | May duplicate similar logic across modules (can be mitigated with shared utilities) |
| **Cross-cutting Concerns** | Harder to see all repositories or all services at once |
| **Shared Code** | Need a strategy for shared/common code |
| **Initial Learning Curve** | Developers used to layered architecture need adjustment |

---

## 🏗️ Recommended Structure for Notification & Reporting Module

Here's the proposed structure for the notification and reporting module:

```
app/
├── modules/                          # OR "domains/" or "features/"
│   │
│   ├── notification/                 # Notification domain module
│   │   ├── __init__.py
│   │   ├── models/                   # Database models (ORM)
│   │   │   ├── __init__.py
│   │   │   ├── notification_delivery.py
│   │   │   ├── notification_preference.py
│   │   │   └── alert_rule.py
│   │   │
│   │   ├── entities/                 # Domain entities (business logic)
│   │   │   ├── __init__.py
│   │   │   ├── notification.py
│   │   │   └── alert_rule.py
│   │   │
│   │   ├── repositories/             # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── notification_repository.py
│   │   │   ├── preference_repository.py
│   │   │   └── alert_rule_repository.py
│   │   │
│   │   ├── services/                 # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── notification_service.py
│   │   │   ├── alert_service.py
│   │   │   └── delivery_tracker_service.py
│   │   │
│   │   ├── schemas/                  # Pydantic DTOs (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── notification_schemas.py
│   │   │   └── alert_schemas.py
│   │   │
│   │   ├── controllers/              # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── notification_controller.py
│   │   │   └── alert_controller.py
│   │   │
│   │   ├── channels/                 # Notification channel implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── email_channel.py
│   │   │   ├── slack_channel.py
│   │   │   ├── webhook_channel.py
│   │   │   └── sms_channel.py
│   │   │
│   │   ├── utils/                    # Module-specific utilities
│   │   │   ├── __init__.py
│   │   │   ├── formatters.py
│   │   │   └── validators.py
│   │   │
│   │   ├── exceptions.py             # Module-specific exceptions
│   │   ├── constants.py              # Module constants/enums
│   │   └── dependencies.py           # FastAPI dependencies for this module
│   │
│   └── reporting/                    # Reporting domain module
│       ├── __init__.py
│       ├── models/                   # Database models
│       │   ├── __init__.py
│       │   ├── report.py
│       │   ├── report_template.py
│       │   └── report_subscription.py
│       │
│       ├── entities/                 # Domain entities
│       │   ├── __init__.py
│       │   └── report.py
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── report_repository.py
│       │   ├── template_repository.py
│       │   └── subscription_repository.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── report_service.py
│       │   ├── template_service.py
│       │   └── subscription_service.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── report_schemas.py
│       │   └── template_schemas.py
│       │
│       ├── controllers/
│       │   ├── __init__.py
│       │   ├── report_controller.py
│       │   └── template_controller.py
│       │
│       ├── generators/               # Report generators
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── pdf_generator.py
│       │   ├── excel_generator.py
│       │   └── template_renderer.py
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── content_builder.py
│       │   └── formatters.py
│       │
│       ├── exceptions.py
│       ├── constants.py
│       └── dependencies.py
│
├── shared/                           # Shared/common code across modules
│   ├── __init__.py
│   ├── database/                     # Shared database utilities
│   ├── logging/                      # Shared logging
│   ├── exceptions/                   # Common exceptions
│   ├── middleware/                   # Common middleware
│   ├── utils/                        # Common utilities
│   └── security/                     # Auth, permissions
│
├── core/                             # Core application (config, startup)
│   ├── __init__.py
│   ├── config.py
│   ├── app.py                        # FastAPI app factory
│   └── dependencies.py               # Global dependencies
│
└── main.py                           # Entry point
```

---

## 🔌 How to Wire Up Routes

With this structure, you'd register routes like this:

### Option 1: In each module's `__init__.py`

```python
# app/modules/notification/__init__.py
from fastapi import APIRouter
from .controllers import notification_controller, alert_controller

router = APIRouter(prefix="/notifications", tags=["Notifications"])
router.include_router(notification_controller.router)
router.include_router(alert_controller.router)
```

```python
# app/modules/reporting/__init__.py
from fastapi import APIRouter
from .controllers import report_controller, template_controller

router = APIRouter(prefix="/reports", tags=["Reports"])
router.include_router(report_controller.router)
router.include_router(template_controller.router)
```

### Then in main app:

```python
# app/core/app.py or main.py
from fastapi import FastAPI
from app.modules.notification import router as notification_router
from app.modules.reporting import router as reporting_router

app = FastAPI()

app.include_router(notification_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
```

---

## 🎯 Alternative: Hybrid Approach

Some teams use a **hybrid approach** combining both:

```
app/
├── modules/
│   ├── notification/         # Feature module (fully encapsulated)
│   └── reporting/            # Feature module (fully encapsulated)
│
├── domain/                   # Shared domain layer
│   ├── entities/             # Shared entities across modules
│   └── value_objects/        # Shared value objects
│
├── infrastructure/           # Shared infrastructure
│   ├── database/
│   ├── cache/
│   └── messaging/
│
└── api/                      # API layer (if you want centralized routing)
    └── v1/
        ├── notification_routes.py
        └── reporting_routes.py
```

---

## 🌟 Recommended Approach for This Project

Given the current architecture (DDD with clean architecture), the recommended approach is:

### **"Package by Feature with Shared Core"**

```
app/
├── modules/                  # ← Feature modules (vertical slices)
│   ├── notification_and_reporting/    # Combined module (tightly coupled)
│   │   ├── notification/
│   │   │   ├── models/
│   │   │   ├── entities/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── schemas/
│   │   │   └── controllers/
│   │   └── reporting/
│   │       ├── models/
│   │       ├── entities/
│   │       ├── repositories/
│   │       ├── services/
│   │       ├── schemas/
│   │       └── controllers/
│
├── domain/                   # ← Keep existing shared domain
│   ├── entities/             # Shared entities (User, Session, etc.)
│   └── value_objects/
│
├── shared/                   # ← Shared infrastructure
│   ├── database/
│   ├── cache/
│   └── utils/
│
└── api/                      # ← Existing API layer (can keep or move to modules)
    └── v1/
```

This gives you:
- ✅ Module isolation for new features
- ✅ Backward compatibility with existing code
- ✅ Gradual migration path
- ✅ Clear boundaries

---

## 📊 Comparison: Package by Layer vs Package by Feature

| Aspect | Package by Layer | Package by Feature |
|--------|------------------|-------------------|
| **Organization** | Horizontal (by technical concern) | Vertical (by business feature) |
| **Cohesion** | Low (related code scattered) | High (related code together) |
| **Coupling** | High (changes affect multiple layers) | Low (changes isolated to module) |
| **Navigation** | Must jump between directories | All code in one place |
| **Team Structure** | Teams organized by layer (backend, frontend) | Teams organized by feature/domain |
| **Scalability** | Harder to extract to microservices | Easier to extract to microservices |
| **DDD Alignment** | Doesn't align well | Aligns with bounded contexts |
| **Learning Curve** | Familiar to most developers | Requires paradigm shift |

---

## 🛠️ Migration Strategy

### Phase 1: Create Module Structure
1. Create `app/modules/` directory
2. Create subdirectories for notification and reporting modules
3. Set up basic structure (models, services, etc.)

### Phase 2: Move Existing Code
1. Move existing `report_service.py` → `modules/reporting/services/`
2. Move existing `report.py` entity → `modules/reporting/entities/`
3. Move existing `report_repository.py` → `modules/reporting/repositories/`
4. Update imports

### Phase 3: Add New Features
1. Implement notification module from scratch in new structure
2. Add new reporting features (templates, PDF generation, etc.)

### Phase 4: Refactor API Layer
1. Create controllers in modules
2. Register routers from modules
3. Gradually migrate API endpoints

---

## 📖 References & Further Reading

1. **"Screaming Architecture"** - Robert C. Martin (Uncle Bob)
   - https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html

2. **"Package by Feature, not Layer"** - Simon Brown
   - https://www.codingthearchitecture.com/2015/03/08/package_by_component_and_architecturally_aligned_testing.html

3. **"Vertical Slice Architecture"** - Jimmy Bogard
   - https://jimmybogard.com/vertical-slice-architecture/

4. **"Modular Monolith"** - Kamil Grzybek
   - https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer

5. **DDD Bounded Contexts** - align modules with bounded contexts
   - https://martinfowler.com/bliki/BoundedContext.html

---

## 💡 Best Practices

### 1. Module Independence
- Each module should be independently deployable (if needed)
- Minimize dependencies between modules
- Use events/messaging for cross-module communication

### 2. Shared Code Strategy
- Create `shared/` directory for truly common code
- Avoid premature extraction to shared
- Prefer duplication over wrong abstraction initially

### 3. Testing
- Each module should have its own tests
- Integration tests should test module boundaries
- End-to-end tests should test complete features

### 4. Documentation
- Each module should have its own README.md
- Document module boundaries and contracts
- Keep architecture decision records (ADRs)

### 5. Dependency Management
```python
# Good: Module dependencies
from app.modules.notification.services import NotificationService

# Good: Shared utilities
from app.shared.database import get_db_session

# Bad: Cross-module domain logic
from app.modules.reporting.services import ReportService  # In notification module
```

### 6. API Versioning
```python
# app/modules/notification/__init__.py
router_v1 = APIRouter(prefix="/api/v1/notifications")
router_v2 = APIRouter(prefix="/api/v2/notifications")
```

---

## ⚠️ Common Pitfalls

1. **Over-modularization**: Don't create a module for every tiny feature
2. **Under-shared**: Don't duplicate database connection logic, auth, etc.
3. **Tight Coupling**: Modules importing directly from each other's internals
4. **Unclear Boundaries**: Not defining clear module responsibilities
5. **God Modules**: Modules that do too much (should be split)

---

## 🎯 When to Use Package by Feature

Use **Package by Feature** when:
- ✅ You have distinct business capabilities/domains
- ✅ Teams are organized around features/products
- ✅ You want to prepare for potential microservices extraction
- ✅ Features have low coupling with each other
- ✅ You want better module isolation

Use **Package by Layer** when:
- ✅ You have a small, simple application
- ✅ All features are tightly coupled
- ✅ Team is organized by technical expertise
- ✅ You have strong framework conventions to follow

---

## Keywords

`package-by-feature`, `vertical-slice-architecture`, `modular-monolith`, `screaming-architecture`, `domain-centric`, `feature-based`, `bounded-context`, `ddd`, `clean-architecture`, `module-organization`, `architecture-pattern`

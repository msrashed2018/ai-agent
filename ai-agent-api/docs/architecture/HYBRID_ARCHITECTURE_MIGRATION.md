# Hybrid Architecture Migration Plan

## Overview

This document describes the **hybrid architecture approach** where new features (notification and reporting) are implemented using **Package by Feature** architecture while existing code remains in the **Layered Architecture**.

This is a **gradual migration strategy** that minimizes risk and allows validation of the new architecture pattern.

---

## 🎯 Goals

1. ✅ Implement notification and reporting as isolated feature modules
2. ✅ Keep existing layered architecture unchanged (no refactoring)
3. ✅ Allow duplication of classes when needed (shared code in both layers)
4. ✅ Provide clear boundaries between old and new architecture
5. ✅ Enable future migration of other features if desired

---

## 🏗️ Hybrid Architecture Structure

```
app/
├── modules/                          # NEW: Package by Feature
│   └── notification_and_reporting/   # New feature module
│       ├── __init__.py
│       ├── notification/
│       │   ├── models/
│       │   ├── entities/
│       │   ├── repositories/
│       │   ├── services/
│       │   ├── schemas/
│       │   ├── controllers/
│       │   ├── channels/
│       │   ├── utils/
│       │   ├── exceptions.py
│       │   ├── constants.py
│       │   └── dependencies.py
│       │
│       └── reporting/
│           ├── models/
│           ├── entities/
│           ├── repositories/
│           ├── services/
│           ├── schemas/
│           ├── controllers/
│           ├── generators/
│           ├── utils/
│           ├── exceptions.py
│           ├── constants.py
│           └── dependencies.py
│
├── api/                              # EXISTING: Layered Architecture
│   ├── v1/
│   │   ├── sessions.py              # Keep existing
│   │   ├── tasks.py                 # Keep existing
│   │   ├── auth.py                  # Keep existing
│   │   └── admin.py                 # Keep existing
│   └── middleware/
│
├── services/                         # EXISTING: Keep all existing services
│   ├── session_service.py
│   ├── task_service.py
│   ├── audit_service.py
│   ├── storage_manager.py
│   └── ...
│
├── repositories/                     # EXISTING: Keep all existing repos
│   ├── session_repository.py
│   ├── task_repository.py
│   ├── user_repository.py
│   └── ...
│
├── domain/                           # EXISTING: Keep existing domain entities
│   ├── entities/
│   │   ├── session.py
│   │   ├── user.py
│   │   ├── task.py
│   │   └── ...
│   └── value_objects/
│
├── models/                           # EXISTING: Keep existing ORM models
│   ├── session.py
│   ├── user.py
│   ├── task.py
│   └── ...
│
├── schemas/                          # EXISTING: Keep existing schemas
│   ├── session.py
│   ├── task.py
│   └── ...
│
├── shared/                           # NEW: Truly shared utilities
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py              # Shared DB session
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py               # Shared logger
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── base.py                 # Common exceptions
│   └── utils/
│       ├── __init__.py
│       └── datetime_utils.py       # Shared utilities
│
├── core/                             # EXISTING: Keep as-is
│   ├── config.py
│   ├── logging.py
│   └── dependencies.py
│
└── main.py                           # EXISTING: Update to register new modules
```

---

## 📋 Migration Strategy

### Phase 1: Setup Module Structure (Week 1)

**Tasks**:
1. Create `app/modules/` directory
2. Create `app/modules/notification_and_reporting/` parent module
3. Create subdirectories for notification and reporting
4. Create `app/shared/` for truly shared code
5. Set up module `__init__.py` files with routers

**No existing code is touched in this phase.**

### Phase 2: Implement Notification Module (Week 2-3)

**Tasks**:
1. Create notification models, entities, repositories
2. Implement notification service and channels
3. Create notification controllers
4. Register notification routes in main app

**Dependencies on existing code**:
- Use existing `User` entity from `app/domain/entities/user.py`
- Use existing `Session` entity from `app/domain/entities/session.py`
- Use existing database session from `app/core/dependencies.py`

### Phase 3: Implement Enhanced Reporting Module (Week 4-5)

**Tasks**:
1. **Option A**: Move existing `report_service.py` to module (breaking change)
2. **Option B**: Duplicate and enhance in module (recommended)
3. Implement templates, PDF generation, subscriptions
4. Create reporting controllers
5. Register reporting routes

**Recommendation**: Use Option B (duplicate) to avoid breaking existing code

### Phase 4: Integration & Testing (Week 6)

**Tasks**:
1. Wire up notification and reporting integration
2. Add comprehensive tests
3. Update API documentation
4. Create migration guide for API consumers

---

## 🔄 Sharing Strategy: What to Share vs Duplicate

### ✅ Always Share (Never Duplicate)

These should be referenced from existing locations:

| Component | Location | Reason |
|-----------|----------|--------|
| **Database session** | `app/database/session.py` | Single source of truth for DB connections |
| **Config** | `app/core/config.py` | Single configuration |
| **Logger** | `app/core/logging.py` | Centralized logging |
| **Auth dependencies** | `app/api/dependencies.py` | Single authentication mechanism |
| **Base exceptions** | `app/domain/exceptions.py` | Common exception hierarchy |
| **User entity** | `app/domain/entities/user.py` | Core domain entity |
| **Session entity** | `app/domain/entities/session.py` | Core domain entity |
| **Task entity** | `app/domain/entities/task.py` | Core domain entity |

### ⚖️ Duplicate When Needed (Keep in Both)

These can be duplicated if the module needs to evolve independently:

| Component | When to Duplicate | Example |
|-----------|-------------------|---------|
| **Value objects** | Module-specific implementations | `NotificationMessage` vs existing `Message` |
| **Enums/Constants** | Module-specific values | `NotificationChannel` enum |
| **DTOs/Schemas** | API contract differs | `NotificationCreateRequest` |
| **Utilities** | Module-specific logic | `notification_formatters.py` |
| **Validators** | Domain-specific validation | `email_validator.py` |

### ❌ Move to Shared (If Used by Both)

If you find existing code is needed by the new module, you have two options:

**Option 1: Import from existing location** (Recommended initially)
```python
# In app/modules/notification_and_reporting/notification/services/notification_service.py
from app.repositories.user_repository import UserRepository  # Use existing
from app.domain.entities.user import User  # Use existing
```

**Option 2: Create shared version** (If it becomes common)
```python
# Move to app/shared/repositories/user_repository.py
# Then both old and new code import from shared
```

---

## 🔌 Wiring Strategy

### Registering Module Routes

**In `app/modules/notification_and_reporting/__init__.py`**:
```python
"""Notification and Reporting Module - Package by Feature Architecture."""
from fastapi import APIRouter

# Import submodule routers
from .notification import router as notification_router
from .reporting import router as reporting_router

# Create parent router for the entire module
router = APIRouter(prefix="/api/v1", tags=["Notification & Reporting"])

# Include submodule routers
router.include_router(notification_router)
router.include_router(reporting_router)

__all__ = ["router"]
```

**In `app/modules/notification_and_reporting/notification/__init__.py`**:
```python
"""Notification submodule."""
from fastapi import APIRouter
from .controllers import notification_controller, alert_controller

router = APIRouter(prefix="/notifications", tags=["Notifications"])
router.include_router(notification_controller.router)
router.include_router(alert_controller.router)

__all__ = ["router"]
```

**In `app/main.py`**:
```python
from fastapi import FastAPI
from app.api.v1 import sessions, tasks, auth, admin  # Existing routes
from app.modules.notification_and_reporting import router as nar_router  # NEW

app = FastAPI(title="AI Agent API")

# Existing routes (unchanged)
app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])

# NEW: Register notification and reporting module
app.include_router(nar_router)
```

---

## 📦 Dependency Injection Strategy

### Module-Specific Dependencies

**In `app/modules/notification_and_reporting/notification/dependencies.py`**:
```python
"""Dependencies for notification module."""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db  # Shared DB session
from app.core.dependencies import get_current_user  # Shared auth
from app.domain.entities.user import User  # Shared entity

from .repositories.notification_repository import NotificationRepository
from .repositories.preference_repository import PreferenceRepository
from .services.notification_service import NotificationService


async def get_notification_repository(
    db: AsyncSession = Depends(get_db)
) -> NotificationRepository:
    """Get notification repository."""
    return NotificationRepository(db)


async def get_preference_repository(
    db: AsyncSession = Depends(get_db)
) -> PreferenceRepository:
    """Get preference repository."""
    return PreferenceRepository(db)


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
    notification_repo: NotificationRepository = Depends(get_notification_repository),
    preference_repo: PreferenceRepository = Depends(get_preference_repository),
) -> NotificationService:
    """Get notification service."""
    return NotificationService(
        db=db,
        notification_repo=notification_repo,
        preference_repo=preference_repo,
    )
```

### Using Dependencies in Controllers

**In `app/modules/notification_and_reporting/notification/controllers/notification_controller.py`**:
```python
"""Notification API endpoints."""
from fastapi import APIRouter, Depends
from uuid import UUID

from app.core.dependencies import get_current_user  # Shared
from app.domain.entities.user import User  # Shared

from ..dependencies import get_notification_service
from ..services.notification_service import NotificationService
from ..schemas.notification_schemas import (
    NotificationCreateRequest,
    NotificationResponse,
)

router = APIRouter()


@router.post("/", response_model=NotificationResponse)
async def send_notification(
    request: NotificationCreateRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Send a notification."""
    notification = await notification_service.send_notification(
        user_id=current_user.id,
        channel=request.channel,
        recipient=request.recipient,
        subject=request.subject,
        content=request.content,
    )
    return notification


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Get notification by ID."""
    return await notification_service.get_notification(
        notification_id=notification_id,
        user_id=current_user.id,
    )
```

---

## 🗄️ Database Models Strategy

### Option 1: Keep Models in Existing Location (Recommended)

**Advantages**:
- Single source of truth
- Alembic migrations in one place
- No duplication

**Implementation**:
```python
# Continue using app/models/notification_delivery.py
# Import in module:
from app.models.notification_delivery import NotificationDeliveryModel
```

### Option 2: Models in Module (Advanced)

**Advantages**:
- Complete module independence
- Can split database schema if needed

**Challenges**:
- Need to configure Alembic to scan multiple directories
- More complex migration management

**Implementation**:
```python
# app/modules/notification_and_reporting/notification/models/notification_delivery.py
# Import in alembic env.py:
from app.modules.notification_and_reporting.notification.models import *
```

**Recommendation**: Start with **Option 1** (keep in `app/models/`) for simplicity.

---

## 🧪 Testing Strategy

### Module-Specific Tests

```
tests/
├── unit/                             # EXISTING: Keep existing tests
│   ├── services/
│   ├── repositories/
│   └── domain/
│
├── integration/                      # EXISTING: Keep existing tests
│   ├── test_sessions_api.py
│   └── test_tasks_api.py
│
├── e2e/                              # EXISTING: Keep existing tests
│   └── test_complete_flows.py
│
└── modules/                          # NEW: Module-specific tests
    └── notification_and_reporting/
        ├── notification/
        │   ├── unit/
        │   │   ├── test_notification_service.py
        │   │   ├── test_email_channel.py
        │   │   └── test_slack_channel.py
        │   ├── integration/
        │   │   └── test_notification_api.py
        │   └── e2e/
        │       └── test_notification_flow.py
        │
        └── reporting/
            ├── unit/
            ├── integration/
            └── e2e/
```

---

## 📝 Documentation Updates

### Module README

Create `app/modules/notification_and_reporting/README.md`:
```markdown
# Notification and Reporting Module

This module is implemented using **Package by Feature** architecture.

## Structure

- `notification/` - Notification delivery system
- `reporting/` - Enhanced reporting system

## Dependencies

### Shared from Layered Architecture
- User entity: `app/domain/entities/user.py`
- Session entity: `app/domain/entities/session.py`
- Database session: `app/database/session.py`
- Auth: `app/core/dependencies.py`

### Module-Specific
- All notification logic is self-contained
- All reporting logic is self-contained

## API Endpoints

- `POST /api/v1/notifications/` - Send notification
- `GET /api/v1/notifications/{id}` - Get notification
- `POST /api/v1/reports/` - Generate report
- `GET /api/v1/reports/{id}` - Get report

## Testing

Run module tests:
```bash
pytest tests/modules/notification_and_reporting/
```
```

---

## ⚠️ Migration Guidelines

### DO ✅

1. **Import shared entities from existing locations**
   ```python
   from app.domain.entities.user import User
   from app.domain.entities.session import Session
   ```

2. **Reuse existing database session**
   ```python
   from app.database.session import get_db
   ```

3. **Reuse existing auth**
   ```python
   from app.core.dependencies import get_current_user
   ```

4. **Create module-specific exceptions**
   ```python
   # app/modules/.../notification/exceptions.py
   class NotificationError(Exception):
       pass
   ```

5. **Keep models in app/models/ initially**
   ```python
   # app/models/notification_delivery.py
   ```

### DON'T ❌

1. **Don't refactor existing code**
   - Leave `app/services/session_service.py` untouched
   - Leave `app/api/v1/sessions.py` untouched

2. **Don't create dependencies between modules**
   ```python
   # BAD: Don't do this
   from app.modules.notification_and_reporting.notification.services import NotificationService
   # in app/services/session_service.py
   ```

3. **Don't duplicate core infrastructure**
   - Don't create separate database connections
   - Don't create separate auth systems

4. **Don't modify existing database models**
   - Create new models for new tables
   - Don't change existing `SessionModel`, `UserModel`, etc.

---

## 🔮 Future Migration Path

If the Package by Feature architecture proves successful, you can gradually migrate existing features:

### Phase 1: New Features Only (Current)
```
app/
├── modules/
│   └── notification_and_reporting/  # New
└── [existing layered code]           # Unchanged
```

### Phase 2: Extract Core Features (Future)
```
app/
├── modules/
│   ├── notification_and_reporting/  # Existing
│   ├── sessions/                     # Migrated
│   └── tasks/                        # Migrated
└── [minimal shared code]
```

### Phase 3: Full Migration (Optional)
```
app/
├── modules/
│   ├── notification_and_reporting/
│   ├── sessions/
│   ├── tasks/
│   ├── auth/
│   └── admin/
└── shared/                           # Only truly shared code
```

---

## 🎯 Success Criteria

The hybrid architecture is successful if:

1. ✅ New notification and reporting features work correctly
2. ✅ Existing features remain unaffected
3. ✅ No breaking changes to existing APIs
4. ✅ Tests pass for both old and new code
5. ✅ Development velocity improves for new features
6. ✅ Code organization is clearer for new features
7. ✅ Team can easily understand and contribute to new modules

---

## 📚 Related Documentation

- [Package by Feature Architecture](./PACKAGE_BY_FEATURE_ARCHITECTURE.md)
- [Current Layered Architecture](./LAYERED_ARCHITECTURE.md)
- [Domain Model](./DOMAIN_MODEL.md)
- [Notification and Reporting Enhancement Plan](../features/notification-and-reporting-enhancement.md)

---

## Keywords

`hybrid-architecture`, `gradual-migration`, `package-by-feature`, `layered-architecture`, `migration-strategy`, `coexistence`, `backward-compatibility`, `module-isolation`

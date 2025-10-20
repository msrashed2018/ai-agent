# AI Agent API Documentation

Complete API documentation organized by functional area.

---

## Directory Structure

```
docs/apis/
├── README.md                    # This file
├── api-inventory.md             # Complete list of all 60 endpoints
├── authentication/              # Authentication APIs (3 endpoints)
│   ├── authentication-management.md
│   └── test_authentication.py
├── monitoring/                  # Monitoring & Health APIs (7 endpoints)
│   ├── monitoring-management.md
│   └── test_monitoring.py
├── sessions/                    # Session Management APIs (17 endpoints)
│   └── session-management.md
├── session-templates/           # Session Template APIs (8 endpoints)
│   └── session-templates-management.md
├── tasks/                       # Task Management APIs (8 endpoints)
│   └── task-management.md
├── reports/                     # Report APIs (3 endpoints)
│   └── report-management.md
├── mcp-servers/                 # MCP Server APIs (9 endpoints)
│   └── mcp-server-management.md
├── admin/                       # Admin APIs (3 endpoints)
│   └── admin-management.md
└── websocket/                   # WebSocket APIs (1 endpoint)
    └── websocket-management.md
```

---

## API Groups

### ✅ Phase 1 - Foundation APIs (Complete)

#### 1. Authentication APIs
**Endpoints:** 3 | **Auth Required:** Partial
**Documentation:** [authentication/authentication-management.md](authentication/authentication-management.md)
**Test Script:** [authentication/test_authentication.py](authentication/test_authentication.py)

- POST `/auth/login` - User authentication
- POST `/auth/refresh` - Token refresh
- GET `/auth/me` - Get current user info

**Key Features:**
- JWT-based authentication
- 6-hour access tokens, 24-hour refresh tokens
- Role-based access (admin, user)

#### 2. Monitoring APIs
**Endpoints:** 7 | **Auth Required:** Partial
**Documentation:** [monitoring/monitoring-management.md](monitoring/monitoring-management.md)
**Test Script:** [monitoring/test_monitoring.py](monitoring/test_monitoring.py)

- GET `/monitoring/health` - Overall system health
- GET `/monitoring/health/database` - Database connectivity
- GET `/monitoring/health/sdk` - Claude SDK availability
- GET `/monitoring/health/storage` - Storage availability
- GET `/monitoring/costs/user/{user_id}` - User costs
- GET `/monitoring/costs/budget/{user_id}` - Budget status
- GET `/monitoring/metrics/session/{session_id}` - Session metrics

**Key Features:**
- No-auth health checks
- Cost tracking per user
- Budget monitoring
- Session metrics

---

### 📝 Phase 2 - Core Session APIs (Pending)

#### 3. Session Management APIs
**Endpoints:** 17 | **Auth Required:** Yes
**Documentation:** Coming soon

**Subgroups:**
- Core operations (5): create, read, list, query, delete
- Control (2): pause, resume
- Data access (3): messages, tool-calls, workdir download
- Advanced (7): fork, archive, hooks, permissions, metrics

#### 4. WebSocket APIs
**Endpoints:** 1 | **Auth Required:** Yes
**Documentation:** Coming soon

- WS `/sessions/{session_id}/stream` - Real-time session streaming

---

### 📝 Phase 3 - Templates & Tasks (Pending)

#### 5. Session Template APIs
**Endpoints:** 8 | **Auth Required:** Yes
**Documentation:** [session-templates/session-templates-management.md](session-templates/session-templates-management.md)

**Subgroups:**
- Management (5): create, read, list, update, delete
- Discovery (2): search, popular
- Sharing (1): update sharing settings

#### 6. Task Management APIs
**Endpoints:** 8 | **Auth Required:** Yes
**Documentation:** Coming soon

**Subgroups:**
- Definition (5): create, read, list, update, delete
- Execution (3): execute, list executions, get execution status

---

### 📝 Phase 4 - Integrations (Pending)

#### 7. MCP Server APIs
**Endpoints:** 9 | **Auth Required:** Yes
**Documentation:** Coming soon

**Subgroups:**
- Management (5): create, read, list, update, delete
- Operations (2): health check, templates
- Import/Export (2): Claude Desktop integration

#### 8. Report APIs
**Endpoints:** 3 | **Auth Required:** Yes
**Documentation:** Coming soon

- GET `/reports/{report_id}` - Get report
- GET `/reports` - List reports
- GET `/reports/{report_id}/download` - Download report

---

### 📝 Phase 5 - Administration (Pending)

#### 9. Admin APIs
**Endpoints:** 3 | **Auth Required:** Yes (Admin Only)
**Documentation:** Coming soon

- GET `/admin/stats` - System statistics
- GET `/admin/sessions` - All sessions
- GET `/admin/users` - All users

---

## Testing

### Quick Start

```bash
# 1. Ensure API server is running
make status

# 2. Start server if needed
make run-bg

# 3. Login as admin
eval $(make login-admin)

# 4. Login as regular user (in separate terminal)
eval $(make login-user)

# 5. Run test scripts
python3 docs/apis/authentication/test_authentication.py
python3 docs/apis/monitoring/test_monitoring.py
```

### Available Test Users

**Admin User:**
- Email: `admin@default.org`
- Password: `admin123`
- Role: `admin`

**Regular User:**
- Email: `user@default.org`
- Password: `user1234`
- Role: `user`

### Environment Variables

After login, these variables are available:

**Admin:**
- `AI_AGENT_ADMIN_ACCESS_TOKEN`
- `AI_AGENT_ADMIN_REFRESH_TOKEN`
- `AI_AGENT_ADMIN_USER_ID`

**User:**
- `AI_AGENT_USER_ACCESS_TOKEN`
- `AI_AGENT_USER_REFRESH_TOKEN`
- `AI_AGENT_USER_USER_ID`

---

## Documentation Standards

Each API group documentation includes:

1. **Endpoint Overview** - Method, path, status codes
2. **cURL Examples** - Real working examples
3. **Request/Response Schemas** - With field descriptions
4. **Backend Processing Steps** - Detailed flow
5. **Error Scenarios** - All possible error responses
6. **Related Files** - Source code locations
7. **Usage Examples** - Common patterns

---

## Progress Tracking

| Phase | API Group | Endpoints | Testing | Documentation | Scripts |
|-------|-----------|-----------|---------|---------------|---------|
| 1 | Authentication | 3 | ✅ | ✅ | ✅ |
| 1 | Monitoring | 7 | ✅ | ✅ | ✅ |
| 2 | Sessions | 17 | ⏳ | ⏳ | ⏳ |
| 2 | WebSocket | 1 | ⏳ | ⏳ | ⏳ |
| 3 | Templates | 8 | ⏳ | ✅ | ⏳ |
| 3 | Tasks | 8 | ⏳ | ⏳ | ⏳ |
| 4 | MCP Servers | 9 | ⏳ | ⏳ | ⏳ |
| 4 | Reports | 3 | ⏳ | ⏳ | ⏳ |
| 5 | Admin | 3 | ⏳ | ⏳ | ⏳ |

**Legend:** ✅ Complete | 🔄 In Progress | ⏳ Pending

**Overall Progress:** 10/59 endpoints (17%) tested and documented

---

## Contributing

When documenting new APIs:

1. Follow the template in existing docs
2. Include real cURL examples
3. Test all scenarios (success + errors)
4. Document backend processing flow
5. Create test script for automation
6. Update this README

---

**Last Updated:** October 20, 2025
**Current Phase:** Phase 1 Complete, Phase 2 Starting
**Next Review:** After Phase 2 completion

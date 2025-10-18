# Authentication Commands

Complete guide for authentication commands with API flow details based on actual implementation.

---

## Command: `auth login`

### CLI Command
```bash
ai-agent auth login --email admin@example.com --password admin123
```

### What Happens in the Backend

#### Step 1: HTTP Request to API
```http
POST /api/v1/auth/login HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin123"
}
```

#### Step 2: API Processing Flow

**Route Handler:** `app/api/v1/auth.py:login()`

1. **Request Validation** (Pydantic)
   - Validates email format (must be valid email)
   - Validates password length (minimum 8 characters)
   - Creates `LoginRequest` schema object

2. **Database Query** (UserRepository)
   ```sql
   SELECT id, email, password_hash, role, is_deleted, created_at
   FROM users
   WHERE email = 'admin@example.com';
   ```

3. **Password Verification** (bcrypt)
   ```python
   bcrypt.checkpw(
       plain_password.encode("utf-8"),
       hashed_password.encode("utf-8")
   )
   ```

4. **User Status Check**
   - Verifies `is_deleted = false`
   - If deleted, returns 403 Forbidden

5. **JWT Token Generation**
   - **Access Token:**
     ```python
     {
       "sub": "550e8400-e29b-41d4-a716-446655440000",  # user_id
       "exp": 1729260000,  # expires in 60 minutes
       "type": "access"
     }
     ```
   - **Refresh Token:**
     ```python
     {
       "sub": "550e8400-e29b-41d4-a716-446655440000",  # user_id
       "exp": 1729864800,  # expires in 7 days
       "type": "refresh"
     }
     ```
   - Both signed with `SECRET_KEY` using HS256 algorithm

#### Step 3: API Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Step 4: CLI Token Storage
- Saves to `~/.ai-agent-cli/config.json`:
```json
{
  "api_url": "http://localhost:8000",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "default_output_format": "table",
  "timeout": 30
}
```

#### Step 5: Claude SDK Integration
**None** - Authentication is purely API-level, no Claude SDK calls.

### Expected Output
```
✓ Successfully logged in as admin@example.com
ℹ Access token expires in 3600 seconds
```

### Test Data
```bash
# Admin user
Email: admin@example.com
Password: admin123

# Regular user
Email: user@example.com
Password: user123
```

---

## Command: `auth whoami`

### CLI Command
```bash
ai-agent auth whoami --format table
```

### What Happens in the Backend

#### Step 1: HTTP Request
```http
GET /api/v1/auth/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Step 2: Authentication Middleware Processing

**Dependency:** `app/api/dependencies.py:get_current_active_user()`

1. **Extract Token**
   - Reads `Authorization` header
   - Extracts token from "Bearer {token}" format

2. **JWT Verification**
   ```python
   payload = jwt.decode(
       token,
       settings.SECRET_KEY,
       algorithms=[settings.JWT_ALGORITHM]
   )
   ```
   - Validates signature
   - Checks expiration (`exp` claim)
   - Extracts `user_id` from `sub` claim

3. **Database Query**
   ```sql
   SELECT id, email, role, created_at
   FROM users
   WHERE id = '550e8400-e29b-41d4-a716-446655440000'
   AND is_deleted = false;
   ```

#### Step 3: API Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "role": "admin",
  "created_at": "2025-01-01T00:00:00"
}
```

#### Step 4: Claude SDK Integration
**None** - Returns cached user information from database.

### Expected Output (Table)
```
┌────────────┬─────────────────────────────────────┐
│        Key │ Value                               │
├────────────┼─────────────────────────────────────┤
│         Id │ 550e8400-e29b-41d4-a716-446655440000│
│      Email │ admin@example.com                   │
│       Role │ admin                               │
│ Created At │ 2025-01-01T00:00:00                 │
└────────────┴─────────────────────────────────────┘
```

---

## Command: `auth refresh`

### CLI Command
```bash
ai-agent auth refresh
```

### What Happens in the Backend

#### Step 1: HTTP Request
```http
POST /api/v1/auth/refresh HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Step 2: API Processing

**Route Handler:** `app/api/v1/auth.py:refresh_access_token()`

1. **Refresh Token Validation**
   ```python
   payload = jwt.decode(
       refresh_token,
       settings.SECRET_KEY,
       algorithms=[settings.JWT_ALGORITHM]
   )
   ```
   - Verifies `type == "refresh"`
   - Checks expiration

2. **User Validation**
   ```sql
   SELECT id, email, is_deleted
   FROM users
   WHERE id = '{user_id}';
   ```
   - Ensures user still exists
   - Checks `is_deleted = false`

3. **New Access Token Generation**
   - Creates new access token (60 min expiration)
   - Does NOT create new refresh token (existing one remains valid)

#### Step 3: API Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Step 4: Claude SDK Integration
**None** - Token refresh is authentication-only.

### Expected Output
```
✓ Access token refreshed successfully
ℹ New token expires in 3600 seconds
```

---

## Command: `auth logout`

### CLI Command
```bash
ai-agent auth logout
```

### What Happens

#### Client-Side Only
- Clears `access_token` from config
- Clears `refresh_token` from config
- No HTTP request to server

**Note:** Tokens remain valid on server until natural expiration.

### Expected Output
```
✓ Successfully logged out
```

---

## Command: `auth status`

### CLI Command
```bash
ai-agent auth status
```

### What Happens

1. **Check Local Config** - Reads `~/.ai-agent-cli/config.json`
2. **If Token Exists** - Makes `GET /api/v1/auth/me` request
3. **Display Status** - Shows authentication state and user info

### Expected Output (Authenticated)
```
✓ Authenticated
ℹ API URL: http://localhost:8000
ℹ Logged in as: admin@example.com (admin)
```

### Expected Output (Not Authenticated)
```
ℹ Not authenticated
ℹ Run 'ai-agent auth login' to authenticate
```

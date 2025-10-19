# Working Directories

## Purpose

Working directories provide isolated file systems for each Claude Code session, enabling the agent to read, write, and manipulate files during query execution. Each session gets its own dedicated directory where all file operations occur, ensuring complete isolation between sessions and preventing accidental cross-session interference.

Working directories are the persistent workspace for Claude's file-based operations:
- **Read/Write Operations**: Agent can create, modify, and delete files
- **Isolation**: Each session has completely separate file space
- **Persistence**: Files survive across queries within a session
- **Archival**: Directories can be compressed and stored long-term
- **Portability**: Archives can be downloaded and restored

Understanding working directory management is critical for:
- Resource planning (disk space requirements)
- Data persistence and recovery
- Compliance and audit trails
- Session isolation and security

---

## Working Directory Purpose

### Isolated File System Per Session

Every session gets a dedicated working directory at creation:

From [session_service.py:76-78](../../app/services/session_service.py:76-78):

```python
# 3. Create working directory
workdir = await self.storage_manager.create_working_directory(session.id)
session.working_directory_path = str(workdir)
```

**Path Pattern**: `/tmp/ai-agent-service/sessions/{session_id}/`

**Example**:
```
Session ID: 550e8400-e29b-41d4-a716-446655440000
Working Directory: /tmp/ai-agent-service/sessions/550e8400-e29b-41d4-a716-446655440000/
```

### Agent Can Read/Write Files

Claude Code's tool ecosystem operates within the working directory:

**Read Tool**:
```python
# Agent reads file from working directory
tool_call = {
  "name": "Read",
  "input": {"file_path": "src/main.py"}
}

# Resolved path: {workdir}/src/main.py
```

**Write Tool**:
```python
# Agent writes file to working directory
tool_call = {
  "name": "Write",
  "input": {
    "file_path": "tests/test_feature.py",
    "content": "import unittest\n..."
  }
}

# Creates: {workdir}/tests/test_feature.py
```

**Bash Tool**:
```bash
# Agent executes commands in working directory context
tool_call = {
  "name": "Bash",
  "input": {"command": "python src/main.py"}
}

# Executes with cwd={workdir}
```

### Persistence Across Queries

Files created in one query persist for subsequent queries:

```
Query 1: "Create a Python module with helper functions"
  → Creates: {workdir}/helpers.py

Query 2: "Add tests for the helper functions"
  → Reads: {workdir}/helpers.py (still there)
  → Creates: {workdir}/test_helpers.py

Query 3: "Run the tests"
  → Executes: pytest {workdir}/test_helpers.py
```

The working directory maintains state throughout the session lifecycle.

### Archival for Long-term Storage

When sessions complete, working directories can be archived:

```
Active Session:
└── /tmp/ai-agent-service/sessions/{session_id}/
    └── [files...]

Archived Session:
└── /tmp/ai-agent-service/archives/{session_id}_20251019_103000.tar.gz
    └── Compressed archive (original deleted)
```

Archives preserve session artifacts for compliance, audit, or later restoration.

---

## Directory Structure

### Base Directory Path

From [config.py:59-61](../../app/core/config.py:59-61):

```python
# Agent Working Directories
agent_workdir_base: Path = Path("/tmp/ai-agent-service/sessions")
agent_workdir_archive: Path = Path("/tmp/ai-agent-service/archives")
reports_dir: Path = Path("/tmp/ai-agent-service/reports")
```

**Default Paths**:
- **Active Sessions**: `/tmp/ai-agent-service/sessions/`
- **Archives**: `/tmp/ai-agent-service/archives/`
- **Reports**: `/tmp/ai-agent-service/reports/`

**Customization via Environment Variables**:
```bash
# .env
AGENT_WORKDIR_BASE=/data/sessions
AGENT_WORKDIR_ARCHIVE=/data/archives
REPORTS_DIR=/data/reports
```

### Session Directory Structure

**Individual Session Layout**:
```
/tmp/ai-agent-service/sessions/{session_id}/
├── src/                      # Source code created by agent
│   ├── main.py
│   ├── utils.py
│   └── config.json
├── tests/                    # Tests created by agent
│   ├── test_main.py
│   └── test_utils.py
├── docs/                     # Documentation generated
│   ├── README.md
│   └── API.md
├── output/                   # Output files
│   ├── report.html
│   └── results.csv
├── .claude_history           # Hidden Claude context (if any)
└── temp/                     # Temporary files
    └── scratch.txt
```

**Key Points**:
- Agent can create arbitrary subdirectories
- No enforced structure (agent organizes as needed)
- Hidden files (starting with `.`) are preserved
- Temporary files may accumulate

### Directory Permissions

**Default Permissions**:
- Created with `mkdir(parents=True, exist_ok=True)`
- Owner: Service account running API
- Permissions: Typically `755` (rwxr-xr-x)

From [storage_manager.py:20-24](../../app/services/storage_manager.py:20-24):

```python
async def create_working_directory(self, session_id: UUID) -> Path:
    """Create a working directory for a session."""
    workdir = self.base_workdir / str(session_id)
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir
```

**Security Considerations**:
- Agent runs with service account permissions
- Cannot access files outside working directory (chroot-like)
- Read/Write tools enforce path restrictions
- Bash tool runs in working directory context

---

## Lifecycle

### Creation: On Session Creation

Working directory is created during session initialization:

From [session_service.py:51-107](../../app/services/session_service.py:51-107):

```python
async def create_session(
    self,
    user_id: UUID,
    mode: SessionMode,
    sdk_options: dict,
    name: Optional[str] = None,
    parent_session_id: Optional[UUID] = None,
) -> Session:
    """Create and initialize a new session."""
    # 1. Validate user quotas
    await self._validate_user_quotas(user_id)

    # 2. Create session entity
    session = Session(
        id=uuid4(),
        user_id=user_id,
        mode=mode,
        sdk_options=sdk_options,
        name=name,
    )

    # 3. Create working directory
    workdir = await self.storage_manager.create_working_directory(session.id)
    session.working_directory_path = str(workdir)

    # 4. Persist session
    # ...
```

**Lifecycle State**: Session moves from CREATED → CONNECTING → ACTIVE

**Directory State**: Empty directory ready for file operations

### Usage: During Tool Execution

Claude's tools interact with the working directory throughout session execution:

**Read Tool** (from agent's perspective):
```python
# Agent wants to read a file
await sdk.execute_tool("Read", {
    "file_path": "src/main.py"
})

# Internally resolves to: {workdir}/src/main.py
```

**Write Tool** (from agent's perspective):
```python
# Agent wants to create a file
await sdk.execute_tool("Write", {
    "file_path": "output/report.md",
    "content": "# Report\n\nAnalysis complete."
})

# Creates: {workdir}/output/report.md
```

**Bash Tool** (executes in workdir context):
```python
# Agent runs command
await sdk.execute_tool("Bash", {
    "command": "ls -la"
})

# Executes: cd {workdir} && ls -la
```

**Tool Integration Example**:

```
Query: "Create a Flask API and test it"

Execution Flow:
1. Write tool: Create app.py
   → {workdir}/app.py created
2. Write tool: Create test_app.py
   → {workdir}/test_app.py created
3. Bash tool: pip install flask pytest
   → Installs in virtual env (if configured)
4. Bash tool: pytest test_app.py
   → Runs tests in {workdir}
5. Read tool: Read test results
   → Reads {workdir}/test_output.txt
```

All operations scoped to working directory.

### Persistence: Throughout Session Lifetime

Files persist as long as session is active:

```
Timeline:
10:00 AM - Session created (workdir empty)
10:05 AM - Query 1: "Create main.py" (file created)
10:15 AM - Query 2: "Create tests" (reads main.py, creates tests)
11:00 AM - Query 3: "Refactor main.py" (modifies existing file)
02:00 PM - Query 4: "Run tests" (uses all previous files)
05:00 PM - Session completed (workdir still exists)
```

**Storage Grows Over Time**:
- Each write operation adds files
- Files not automatically cleaned up
- Directory size can grow to max_working_dir_size_mb

### Cleanup: On Session Termination/Archival

When session ends, working directory is handled based on configuration:

**Option 1: Archive and Delete** (default):

From [session_service.py:221-233](../../app/services/session_service.py:221-233):

```python
async def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
    """Soft delete a session."""
    session = await self.get_session(session_id, user_id)

    # Archive working directory if exists
    if session.working_directory_path:
        await self.storage_manager.archive_working_directory(session_id)

    # Soft delete
    success = await self.session_repo.soft_delete(session_id)
    await self.db.commit()

    return success
```

**Process**:
1. Compress working directory to .tar.gz
2. Move archive to `/tmp/ai-agent-service/archives/`
3. Delete original working directory
4. Update session status to ARCHIVED

**Option 2: Delete Without Archive**:

From [storage_manager.py:33-39](../../app/services/storage_manager.py:33-39):

```python
async def delete_working_directory(self, session_id: UUID) -> bool:
    """Delete a session's working directory."""
    workdir = self.base_workdir / str(session_id)
    if workdir.exists():
        shutil.rmtree(workdir)
        return True
    return False
```

**When to Use**:
- Session failed early (nothing valuable)
- Temporary test sessions
- Storage space critical

**Option 3: Keep Indefinitely** (not recommended):
- Working directory remains on disk
- Consumes storage until manually cleaned
- Useful for debugging

### Archival: Compression and Storage

Archival creates compressed backup of working directory:

From [storage_manager.py:41-60](../../app/services/storage_manager.py:41-60):

```python
async def archive_working_directory(self, session_id: UUID) -> Optional[Path]:
    """Archive a session's working directory to tar.gz."""
    workdir = self.base_workdir / str(session_id)
    if not workdir.exists():
        return None

    # Create archive directory if it doesn't exist
    self.archive_dir.mkdir(parents=True, exist_ok=True)

    # Create tar.gz archive
    archive_name = f"{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    archive_path = self.archive_dir / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(workdir, arcname=str(session_id))

    # Delete original directory
    shutil.rmtree(workdir)

    return archive_path
```

**Archive Naming**:
```
{session_id}_{YYYYMMDD_HHMMSS}.tar.gz

Example:
550e8400-e29b-41d4-a716-446655440000_20251019_143022.tar.gz
```

**Compression Ratio**:
- Text files: 80-90% reduction
- Binary files: 10-30% reduction
- Average: 60-70% reduction

**Example**:
```
Original: 500 MB working directory
Archived: 150 MB .tar.gz (70% reduction)
Savings: 350 MB disk space
```

---

## StorageManager

The `StorageManager` service handles all working directory operations.

**Implementation**: [storage_manager.py](../../app/services/storage_manager.py)

### create_working_directory(session_id)

From [storage_manager.py:20-24](../../app/services/storage_manager.py:20-24):

```python
async def create_working_directory(self, session_id: UUID) -> Path:
    """Create a working directory for a session."""
    workdir = self.base_workdir / str(session_id)
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir
```

**Parameters**:
- `session_id`: UUID of session

**Returns**: Path object pointing to created directory

**Behavior**:
- Creates directory if doesn't exist
- No error if already exists (idempotent)
- Creates parent directories if needed
- Returns absolute path

**Example Usage**:
```python
storage_manager = StorageManager()
workdir = await storage_manager.create_working_directory(session.id)

print(workdir)
# /tmp/ai-agent-service/sessions/550e8400-e29b-41d4-a716-446655440000
```

### clone_working_directory(source_id, target_id)

**Not a direct method**, but implemented in session forking:

From [session_service.py:375-387](../../app/services/session_service.py:375-387):

```python
# Copy all files from parent to forked session
for item in parent_workdir.rglob("*"):
    if item.is_file():
        rel_path = item.relative_to(parent_workdir)
        dest_path = forked_workdir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_path)
```

**Parameters**:
- `source_id`: Parent session ID
- `target_id`: Forked session ID

**Returns**: None (modifies file system)

**Behavior**:
- Recursively copies all files from source to target
- Preserves directory structure
- Preserves file metadata (timestamps, permissions)
- Creates target directory structure as needed

**Example**:
```
Source: /sessions/parent-123/
├── src/main.py
└── tests/test.py

Target: /sessions/fork-456/
├── src/main.py  (copied)
└── tests/test.py  (copied)
```

See [SESSION_FORKING.md](SESSION_FORKING.md) for detailed forking process.

### archive_working_directory(session_id, compression)

From [storage_manager.py:41-60](../../app/services/storage_manager.py:41-60):

```python
async def archive_working_directory(self, session_id: UUID) -> Optional[Path]:
    """Archive a session's working directory to tar.gz."""
    workdir = self.base_workdir / str(session_id)
    if not workdir.exists():
        return None

    # Create archive directory if it doesn't exist
    self.archive_dir.mkdir(parents=True, exist_ok=True)

    # Create tar.gz archive
    archive_name = f"{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    archive_path = self.archive_dir / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(workdir, arcname=str(session_id))

    # Delete original directory
    shutil.rmtree(workdir)

    return archive_path
```

**Parameters**:
- `session_id`: UUID of session to archive

**Returns**: Path to created archive, or None if workdir doesn't exist

**Behavior**:
1. Check if working directory exists
2. Create archive directory if needed
3. Create tar.gz archive with timestamp
4. Add all files recursively
5. Delete original working directory
6. Return archive path

**Example Usage**:
```python
archive_path = await storage_manager.archive_working_directory(session.id)

if archive_path:
    print(f"Archived to: {archive_path}")
    # /tmp/ai-agent-service/archives/session-id_20251019_143022.tar.gz
else:
    print("No working directory to archive")
```

**Compression Options** (currently hardcoded to gzip):
- `w:gz` - Gzip compression (default)
- `w:bz2` - Bzip2 compression (higher compression, slower)
- `w:xz` - LZMA compression (highest compression, slowest)

Future enhancement could make compression configurable.

### delete_working_directory(session_id)

From [storage_manager.py:33-39](../../app/services/storage_manager.py:33-39):

```python
async def delete_working_directory(self, session_id: UUID) -> bool:
    """Delete a session's working directory."""
    workdir = self.base_workdir / str(session_id)
    if workdir.exists():
        shutil.rmtree(workdir)
        return True
    return False
```

**Parameters**:
- `session_id`: UUID of session

**Returns**: Boolean indicating if directory was deleted

**Behavior**:
- Deletes directory and all contents recursively
- No error if directory doesn't exist
- Returns True if deleted, False if not found

**Warning**: Permanent deletion - cannot be undone!

**Example Usage**:
```python
# Delete failed session workdir
if session.status == SessionStatus.FAILED:
    deleted = await storage_manager.delete_working_directory(session.id)
    if deleted:
        logger.info(f"Cleaned up failed session {session.id}")
```

### get_directory_size(session_id)

From [storage_manager.py:62-75](../../app/services/storage_manager.py:62-75):

```python
async def get_directory_size(self, session_id: UUID) -> int:
    """Get total size of working directory in bytes."""
    workdir = self.base_workdir / str(session_id)
    if not workdir.exists():
        return 0

    total_size = 0
    for dirpath, dirnames, filenames in os.walk(workdir):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            total_size += filepath.stat().st_size

    return total_size
```

**Parameters**:
- `session_id`: UUID of session

**Returns**: Total size in bytes (int)

**Behavior**:
- Recursively walks directory tree
- Sums file sizes
- Returns 0 if directory doesn't exist
- Does not include directory metadata overhead

**Example Usage**:
```python
size_bytes = await storage_manager.get_directory_size(session.id)
size_mb = size_bytes / (1024 * 1024)

print(f"Working directory: {size_mb:.2f} MB")

# Check against quota
if size_mb > settings.max_working_dir_size_mb:
    raise QuotaExceededError(f"Directory size {size_mb}MB exceeds limit")
```

---

## Tool Integration

### How Read Tool Accesses Files

When Claude uses the Read tool, the file path is resolved relative to the working directory:

```python
# Agent's tool call
{
  "name": "Read",
  "input": {
    "file_path": "src/main.py"
  }
}

# Internal resolution
working_directory = Path(session.working_directory_path)  # /tmp/.../session-id/
absolute_path = working_directory / "src/main.py"
# → /tmp/ai-agent-service/sessions/session-id/src/main.py

# Security check: Ensure path is within working directory
if not absolute_path.is_relative_to(working_directory):
    raise SecurityError("Path traversal attempt detected")

# Read file
with open(absolute_path, 'r') as f:
    content = f.read()
```

**Path Resolution Rules**:
- Relative paths resolved from working directory root
- Absolute paths rejected (security)
- Parent directory references (`../`) checked and rejected if outside workdir
- Symlinks followed but must stay within workdir

### How Write Tool Creates Files

Write tool creates or overwrites files in the working directory:

```python
# Agent's tool call
{
  "name": "Write",
  "input": {
    "file_path": "output/report.md",
    "content": "# Report\n\nData analysis complete."
  }
}

# Internal processing
working_directory = Path(session.working_directory_path)
absolute_path = working_directory / "output/report.md"

# Security check
if not absolute_path.is_relative_to(working_directory):
    raise SecurityError("Path traversal attempt")

# Create parent directories if needed
absolute_path.parent.mkdir(parents=True, exist_ok=True)

# Write file
with open(absolute_path, 'w') as f:
    f.write(content)
```

**Write Behavior**:
- Creates parent directories automatically
- Overwrites existing files
- No backup of overwritten content
- File permissions: Inherits from process

### How Bash Tool Executes in Workdir

Bash commands execute with working directory as current directory:

```python
# Agent's tool call
{
  "name": "Bash",
  "input": {
    "command": "python src/main.py"
  }
}

# Internal execution
working_directory = Path(session.working_directory_path)

# Execute with cwd set to working directory
import subprocess
result = subprocess.run(
    command,
    cwd=str(working_directory),
    shell=True,
    capture_output=True,
    text=True
)
```

**Bash Tool Characteristics**:
- Commands execute in working directory context
- Relative paths resolve from working directory
- Can read/write files in working directory
- Cannot access files outside working directory (unless absolute paths)
- Environment variables can be set per session

**Example**:
```bash
# Agent runs: "ls -la"
# Executes as: cd /tmp/.../session-id && ls -la
# Output: Shows files in working directory
```

### Path Resolution and Security

**Security Constraints**:

1. **No Path Traversal**:
```python
# Blocked: Attempts to escape working directory
"../../../etc/passwd"  # Rejected
"/etc/passwd"          # Rejected
"~/.ssh/id_rsa"        # Rejected
```

2. **Working Directory Jail**:
```python
# Allowed: Within working directory
"src/main.py"          # ✓
"./output/data.csv"    # ✓
"tests/../src/util.py" # ✓ (resolves to src/util.py)
```

3. **Symlink Restrictions**:
```python
# If symlink points outside workdir → Rejected
ln -s /etc/passwd workdir/secret
cat workdir/secret  # Blocked
```

**Implementation** (conceptual):
```python
def resolve_safe_path(base_dir: Path, user_path: str) -> Path:
    """Resolve user path safely within base directory."""
    # Resolve to absolute path
    resolved = (base_dir / user_path).resolve()

    # Check if within base directory
    if not resolved.is_relative_to(base_dir):
        raise SecurityError(f"Path {user_path} escapes working directory")

    return resolved
```

---

## Isolation

### Per-Session Isolation

Each session operates in complete isolation:

```
Session A: /sessions/session-a/
├── data.csv
└── script.py

Session B: /sessions/session-b/
├── data.csv  (different file, same name)
└── script.py  (different file, same name)
```

**No Cross-Session Access**:
- Session A cannot read files from Session B
- Session B cannot modify files in Session A
- Identical filenames don't conflict (different directories)

**Example**:
```python
# Session A
await client.execute_tool("Write", {
    "file_path": "config.json",
    "content": '{"mode": "production"}'
})

# Session B (different user, different session)
await client.execute_tool("Write", {
    "file_path": "config.json",
    "content": '{"mode": "development"}'
})

# Two separate files:
# /sessions/session-a/config.json → {"mode": "production"}
# /sessions/session-b/config.json → {"mode": "development"}
```

### User-Level Isolation

Sessions belong to users, providing user-level data separation:

From [session.py:17](../../app/models/session.py:17):

```python
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
```

**Authorization Checks**:

From [session_service.py:109-122](../../app/services/session_service.py:109-122):

```python
async def get_session(self, session_id: UUID, user_id: UUID) -> Session:
    """Get session by ID with authorization check."""
    session_model = await self.session_repo.get_by_id(session_id)
    if not session_model:
        raise SessionNotFoundError(f"Session {session_id} not found")

    # Check authorization - simple ownership check
    # Admin users can access all sessions, regular users only their own
    user_model = await self.user_repo.get_by_id(user_id)
    if session_model.user_id != user_id and user_model.role != "admin":
        raise PermissionDeniedError("Not authorized to access this session")

    return self._model_to_entity(session_model)
```

**User Isolation Rules**:
- Users can only access their own sessions
- Admin users can access all sessions
- Working directories tied to sessions (and thus users)
- No direct file system access - must go through API

### Security Boundaries

**Multiple Layers of Protection**:

1. **API Authorization**:
```python
# JWT token validates user identity
# Session ownership checked before any operation
```

2. **Path Validation**:
```python
# All file paths validated against working directory
# Path traversal attempts rejected
```

3. **File System Permissions**:
```bash
# Working directories owned by service account
# Users cannot directly access file system
```

4. **Process Isolation**:
```python
# Bash commands run as service account
# Cannot escalate privileges
# Cannot access other sessions' processes
```

### No Cross-Session Access

**Design Principle**: Sessions are hermetically sealed.

**Prevented Scenarios**:

1. **Read Other Session's Files**:
```python
# Session A tries to read Session B's file
await client.execute_tool("Read", {
    "file_path": "../session-b/secret.txt"
})
# → Rejected: Path traversal detected
```

2. **Modify Other Session's Files**:
```python
# Session A tries to delete Session B's file
await client.execute_tool("Bash", {
    "command": "rm -rf ../session-b/"
})
# → Executes in session-a workdir, affects nothing outside
```

3. **Symlink to Other Session**:
```python
# Create symlink to another session
await client.execute_tool("Bash", {
    "command": "ln -s /sessions/session-b ./other_session"
})
# Symlink created, but Read/Write tools reject following it
```

**Exception**: Admin users via API can access all sessions, but still through controlled API endpoints, not direct file system access.

---

## Size Limits

### max_working_dir_size_mb Configuration

From [config.py:56](../../app/core/config.py:56):

```python
max_working_dir_size_mb: int = 1024  # 1GB default
```

**Purpose**: Prevent runaway disk usage

**Default**: 1GB (1024 MB)

**Customization**:
```bash
# .env
MAX_WORKING_DIR_SIZE_MB=2048  # 2GB limit
```

**Per-User Limits** (future enhancement):
```python
# User model could have custom quota
user.max_working_dir_size_mb = 5120  # 5GB for premium users
```

### Quota Enforcement

**Enforcement Points**:

1. **Before File Write**:
```python
async def write_file(session_id, path, content):
    # Check current size
    current_size = await storage_manager.get_directory_size(session_id)
    content_size = len(content.encode('utf-8'))
    projected_size = current_size + content_size

    if projected_size > settings.max_working_dir_size_mb * 1024 * 1024:
        raise QuotaExceededError(
            f"Writing {content_size} bytes would exceed quota "
            f"(current: {current_size}, limit: {settings.max_working_dir_size_mb}MB)"
        )

    # Proceed with write
    ...
```

2. **Periodic Checks**:
```python
# Background task checks all sessions
async def check_session_quotas():
    sessions = await session_repo.get_active_sessions()

    for session in sessions:
        size = await storage_manager.get_directory_size(session.id)
        size_mb = size / (1024 * 1024)

        if size_mb > settings.max_working_dir_size_mb:
            await notify_user_quota_exceeded(session.user_id, session.id, size_mb)
```

3. **Before Session Fork**:
```python
async def fork_session(parent_id):
    parent_size = await storage_manager.get_directory_size(parent_id)
    parent_size_mb = parent_size / (1024 * 1024)

    if parent_size_mb > settings.max_working_dir_size_mb:
        raise QuotaExceededError(
            f"Parent session ({parent_size_mb}MB) exceeds limit, cannot fork"
        )

    # Proceed with fork (will double storage usage)
```

### Cleanup Triggers

**Automatic Cleanup Scenarios**:

**1. Session Completion**:
```python
# When session completes successfully
session.transition_to(SessionStatus.COMPLETED)

# Trigger archival (configurable delay)
await schedule_archival(session.id, delay_hours=24)
```

**2. Session Failure**:
```python
# When session fails
session.transition_to(SessionStatus.FAILED)

# Option A: Archive for debugging
await storage_manager.archive_working_directory(session.id)

# Option B: Delete immediately (if no value)
await storage_manager.delete_working_directory(session.id)
```

**3. Session Termination**:
```python
# When user terminates session
session.transition_to(SessionStatus.TERMINATED)

# Archive working directory
await storage_manager.archive_working_directory(session.id)
```

**4. Scheduled Cleanup**:
```python
# Background job cleans old completed sessions
async def cleanup_old_sessions():
    cutoff = datetime.utcnow() - timedelta(days=settings.session_archive_days)

    old_sessions = await session_repo.get_completed_before(cutoff)

    for session in old_sessions:
        # Archive if not already archived
        if not session.archive_id:
            await storage_manager.archive_working_directory(session.id)

        # Delete archive after retention period
        if session.archived_at < archive_retention_cutoff:
            await delete_archive(session.archive_id)
```

From [config.py:66](../../app/core/config.py:66):
```python
session_archive_days: int = 180  # 6 months
```

**Manual Cleanup**:
```bash
# Admin endpoint
DELETE /api/v1/admin/sessions/{id}/workdir

# Force delete without archive
DELETE /api/v1/admin/sessions/{id}/workdir?force=true
```

---

## Archival

### When to Archive

**Automatic Archival Triggers**:

1. **Session Deletion**:
From [session_service.py:226-227](../../app/services/session_service.py:226-227):
```python
if session.working_directory_path:
    await self.storage_manager.archive_working_directory(session_id)
```

2. **Session Completion** (configurable):
```python
# After session completes, archive after delay
if session.status == SessionStatus.COMPLETED:
    await schedule_task(
        task="archive_session",
        session_id=session.id,
        delay_hours=settings.archive_delay_hours  # e.g., 24 hours
    )
```

3. **Manual Archive Request**:
```bash
POST /api/v1/sessions/{id}/archive
```

4. **Scheduled Archival**:
```python
# Daily job archives old completed sessions
@celery.task
async def archive_old_sessions():
    cutoff = datetime.utcnow() - timedelta(days=7)
    sessions = await session_repo.get_completed_before(cutoff)

    for session in sessions:
        if not session.archive_id:
            await storage_manager.archive_working_directory(session.id)
```

**Manual Archival Reasons**:
- Preserve important work before session deletion
- Free up disk space during active session
- Create backup before risky operations
- Compliance/audit requirements

### Compression Formats

**Current Implementation**: tar.gz (gzip)

From [storage_manager.py:54](../../app/services/storage_manager.py:54):
```python
with tarfile.open(archive_path, "w:gz") as tar:
    tar.add(workdir, arcname=str(session_id))
```

**Available Formats**:

| Format | Python Flag | Extension | Compression | Speed | Use Case |
|--------|-------------|-----------|-------------|-------|----------|
| **gzip** | `w:gz` | `.tar.gz` | Good (70%) | Fast | **Default** |
| bzip2 | `w:bz2` | `.tar.bz2` | Better (75%) | Medium | High compression |
| LZMA/xz | `w:xz` | `.tar.xz` | Best (80%) | Slow | Maximum compression |
| None | `w` | `.tar` | None (0%) | Fastest | Network transfer |

**Configurable Compression** (future enhancement):

From [config.py:116](../../app/core/config.py:116):
```python
archive_compression: str = "gzip"  # 'gzip', 'bzip2', 'xz', 'none'
```

**Example: Configurable Compression**:
```python
async def archive_working_directory(
    self,
    session_id: UUID,
    compression: str = "gzip"
) -> Optional[Path]:
    """Archive with configurable compression."""

    compression_modes = {
        "gzip": "w:gz",
        "bzip2": "w:bz2",
        "xz": "w:xz",
        "none": "w",
    }

    mode = compression_modes.get(compression, "w:gz")
    extension = {
        "w:gz": ".tar.gz",
        "w:bz2": ".tar.bz2",
        "w:xz": ".tar.xz",
        "w": ".tar",
    }[mode]

    archive_name = f"{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{extension}"
    archive_path = self.archive_dir / archive_name

    with tarfile.open(archive_path, mode) as tar:
        tar.add(workdir, arcname=str(session_id))
```

### Archive Storage Location

**Default**: Local filesystem

From [config.py:60](../../app/core/config.py:60):
```python
agent_workdir_archive: Path = Path("/tmp/ai-agent-service/archives")
```

**Archive Path Structure**:
```
/tmp/ai-agent-service/archives/
├── {session_id_1}_20251019_100000.tar.gz
├── {session_id_2}_20251019_110000.tar.gz
├── {session_id_3}_20251019_120000.tar.gz
└── ...
```

**Archive Naming Convention**:
```
{session_id}_{YYYYMMDD_HHMMSS}.tar.gz

Parts:
- session_id: Full UUID of session
- YYYYMMDD: Archive creation date
- HHMMSS: Archive creation time
- .tar.gz: Compression format

Example:
550e8400-e29b-41d4-a716-446655440000_20251019_143022.tar.gz
```

**S3 Storage** (future enhancement):

From [config.py:110-113](../../app/core/config.py:110-113):
```python
storage_provider: str = "filesystem"  # 'filesystem' or 's3'
aws_s3_bucket: str = "ai-agent-archives"
aws_s3_region: str = "us-east-1"
aws_s3_archive_prefix: str = "archives/"
```

**S3 Archive Path** (when implemented):
```
s3://ai-agent-archives/archives/{user_id}/{session_id}/{timestamp}.tar.gz

Example:
s3://ai-agent-archives/archives/user-123/session-456/20251019_143022.tar.gz
```

### Archive Metadata

**Database Model**:

From [working_directory_archive.py:11-53](../../app/models/working_directory_archive.py:11-53):

```python
class WorkingDirectoryArchiveModel(Base):
    """Working directory archive table model."""

    __tablename__ = "working_directory_archives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Archive Location
    archive_path = Column(Text, nullable=False)  # S3 path or filesystem path
    storage_backend = Column(String(50), nullable=False)  # 's3', 'filesystem'

    # Archive Format
    compression_type = Column(String(50), nullable=False)  # 'zip', 'tar.gz', 'tar.bz2'

    # Size Metrics
    size_bytes = Column(BigInteger, nullable=False)

    # Status
    status = Column(String(50), nullable=False, default="pending", index=True)  # 'pending', 'in_progress', 'completed', 'failed'

    # Error Handling
    error_message = Column(Text)

    # Additional Metadata
    archive_metadata = Column(JSONB, default={})  # File counts, directory structure summary, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))
```

**Metadata Fields**:
- `archive_path`: Full path to archive file
- `storage_backend`: "filesystem" or "s3"
- `compression_type`: "tar.gz", "tar.bz2", "tar.xz"
- `size_bytes`: Archive file size
- `status`: "pending" | "in_progress" | "completed" | "failed"
- `archive_metadata`: JSON with file counts, structure summary

**Archive Metadata JSON Example**:
```json
{
  "file_count": 42,
  "total_size_bytes": 524288000,
  "compression_ratio": 0.68,
  "top_level_dirs": ["src", "tests", "docs", "output"],
  "file_types": {
    ".py": 35,
    ".md": 4,
    ".json": 2,
    ".txt": 1
  },
  "largest_files": [
    {"path": "output/data.csv", "size": 104857600},
    {"path": "src/model.pkl", "size": 52428800}
  ]
}
```

### Archive Retrieval

**Get Archive Metadata**:

From [sessions.py:828-873](../../app/api/v1/sessions.py:828-873):

```python
@router.get("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def get_session_archive(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveMetadataResponse:
    """Get archive metadata for a session."""

    # Get archive metadata
    archive_repo = WorkingDirectoryArchiveRepository(db)
    archives = await archive_repo.get_by_session(str(session_id))

    if not archives:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive found for session {session_id}",
        )

    archive = archives[0]  # Get most recent
    return ArchiveMetadataResponse.model_validate(archive)
```

**Download Archive**:

```bash
GET /api/v1/sessions/{id}/workdir/download
```

From [sessions.py:638-698](../../app/api/v1/sessions.py:638-698):

```python
@router.get("/{session_id}/workdir/download")
async def download_working_directory(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Download session working directory as tar.gz archive."""

    # Check if working directory exists
    workdir_path = Path(session.working_directory)
    if not workdir_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Working directory not found",
        )

    # Create tar.gz archive in temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")

    try:
        with tarfile.open(temp_file.name, "w:gz") as tar:
            tar.add(workdir_path, arcname=workdir_path.name)

        # Create streaming response
        def iterfile():
            with open(temp_file.name, "rb") as f:
                yield from f

        filename = f"{session_id}-workdir.tar.gz"

        return StreamingResponse(
            iterfile(),
            media_type="application/gzip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
    finally:
        # Schedule cleanup
        asyncio.create_task(_cleanup_temp_file(temp_file.name))
```

**Restore from Archive** (future):

```python
async def restore_from_archive(session_id: UUID, extract_to: Optional[Path] = None):
    """Restore working directory from archive."""

    # Get archive metadata
    archive = await archive_repo.get_by_session(session_id)

    # Extract archive
    extract_path = extract_to or storage_manager.base_workdir / str(session_id)

    with tarfile.open(archive.archive_path, "r:gz") as tar:
        tar.extractall(extract_path)

    return extract_path
```

### Retention Policies

**Configuration**:

From [config.py:118](../../app/core/config.py:118):
```python
archive_retention_days: int = 90  # 3 months
```

**Cleanup Old Archives**:

From [storage_manager.py:181-195](../../app/services/storage_manager.py:181-195):

```python
async def cleanup_old_archives(self, days: int = 180) -> int:
    """Delete archives older than specified days. Returns count of deleted archives."""
    if not self.archive_dir.exists():
        return 0

    cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
    deleted_count = 0

    for archive_file in self.archive_dir.glob("*.tar.gz"):
        if archive_file.stat().st_mtime < cutoff_time:
            archive_file.unlink()
            deleted_count += 1

    return deleted_count
```

**Scheduled Cleanup**:
```python
@celery.task
async def cleanup_expired_archives():
    """Daily task to clean up expired archives."""
    storage_manager = StorageManager()

    deleted = await storage_manager.cleanup_old_archives(
        days=settings.archive_retention_days
    )

    logger.info(f"Deleted {deleted} expired archives")
```

**Retention Policy Matrix**:

| Session State | Working Directory | Archive | Retention |
|---------------|-------------------|---------|-----------|
| ACTIVE | Keep | None | Until completed |
| COMPLETED | Keep 24h, then archive | Create | 90 days |
| FAILED | Archive or delete | Optional | 30 days |
| TERMINATED | Archive | Create | 90 days |
| ARCHIVED | Deleted | Keep | 90 days |

---

## Storage Backends

### Local Filesystem (Default)

**Current Implementation**: All storage on local filesystem

**Advantages**:
- Simple implementation
- Fast access
- No external dependencies
- No API costs

**Disadvantages**:
- Limited to single server
- No automatic replication
- Manual backup required
- Disk space constraints

**Configuration**:

From [config.py:110](../../app/core/config.py:110):
```python
storage_provider: str = "filesystem"
```

**Directory Structure**:
```
/tmp/ai-agent-service/
├── sessions/              # Active working directories
│   ├── session-1/
│   ├── session-2/
│   └── ...
├── archives/              # Archived sessions
│   ├── session-1_20251019_100000.tar.gz
│   ├── session-2_20251019_110000.tar.gz
│   └── ...
└── reports/               # Generated reports
    ├── report-1.html
    └── ...
```

### S3 Storage (Planned)

**Future Enhancement**: Store archives in S3

**Advantages**:
- Unlimited scalability
- Automatic replication
- Versioning support
- Lifecycle policies
- Cross-region availability

**Configuration**:

From [config.py:110-115](../../app/core/config.py:110-115):
```python
storage_provider: str = "s3"  # 'filesystem' or 's3'
aws_s3_bucket: str = "ai-agent-archives"
aws_s3_region: str = "us-east-1"
aws_s3_archive_prefix: str = "archives/"
aws_access_key_id: str = ""
aws_secret_access_key: str = ""
```

**Planned Implementation**:
```python
class S3StorageBackend:
    """S3 storage backend for archives."""

    async def upload_archive(self, local_path: Path, session_id: UUID) -> str:
        """Upload archive to S3."""
        import boto3

        s3 = boto3.client(
            's3',
            region_name=settings.aws_s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

        # S3 key
        key = f"{settings.aws_s3_archive_prefix}{session_id}/{local_path.name}"

        # Upload
        s3.upload_file(
            str(local_path),
            settings.aws_s3_bucket,
            key,
        )

        # Return S3 URI
        return f"s3://{settings.aws_s3_bucket}/{key}"

    async def download_archive(self, s3_uri: str, local_path: Path) -> Path:
        """Download archive from S3."""
        import boto3

        s3 = boto3.client('s3')

        # Parse S3 URI
        bucket, key = s3_uri.replace("s3://", "").split("/", 1)

        # Download
        s3.download_file(bucket, key, str(local_path))

        return local_path
```

**S3 Lifecycle Policy** (example):
```json
{
  "Rules": [
    {
      "Id": "ArchiveToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

**Cost Estimation**:
- S3 Standard: $0.023/GB/month
- S3 Glacier: $0.004/GB/month
- Data transfer: $0.09/GB (out)

Example: 1000 sessions × 100MB each = 100GB
- S3 Standard: $2.30/month
- S3 Glacier: $0.40/month

### Archive Retention Policies

**Automatic Lifecycle**:

```python
class ArchiveLifecycleManager:
    """Manage archive lifecycle across storage backends."""

    async def apply_retention_policy(self):
        """Apply retention policies to all archives."""

        archive_repo = WorkingDirectoryArchiveRepository(db)

        # Get all completed archives
        archives = await archive_repo.get_by_status("completed")

        for archive in archives:
            age_days = (datetime.utcnow() - archive.created_at).days

            # Policy 1: Move to cold storage after 30 days
            if age_days > 30 and archive.storage_backend == "filesystem":
                await self.migrate_to_s3(archive)

            # Policy 2: Move to Glacier after 90 days
            if age_days > 90 and archive.storage_backend == "s3":
                await self.migrate_to_glacier(archive)

            # Policy 3: Delete after retention period
            if age_days > settings.archive_retention_days:
                await self.delete_archive(archive)
```

**Retention Tiers**:

| Age | Storage | Cost | Access Time |
|-----|---------|------|-------------|
| 0-30 days | Local FS | Included | Immediate |
| 30-90 days | S3 Standard | $0.023/GB/mo | Seconds |
| 90-365 days | S3 Glacier | $0.004/GB/mo | Minutes-Hours |
| 365+ days | Deleted | $0 | N/A |

---

## Configuration

### agent_workdir_base Setting

From [config.py:59](../../app/core/config.py:59):

```python
agent_workdir_base: Path = Path("/tmp/ai-agent-service/sessions")
```

**Purpose**: Base directory for all active session working directories

**Default**: `/tmp/ai-agent-service/sessions`

**Customization**:
```bash
# .env
AGENT_WORKDIR_BASE=/data/sessions
```

**Production Recommendation**:
- Use dedicated disk/volume
- Mount on high-performance storage (SSD)
- Separate from OS disk
- Enable disk quotas

**Example Production Setup**:
```bash
# Mount dedicated volume
/dev/sdb1 on /data/sessions type ext4 (rw,nosuid,nodev,noexec)

# .env
AGENT_WORKDIR_BASE=/data/sessions
```

### agent_workdir_archive Setting

From [config.py:60](../../app/core/config.py:60):

```python
agent_workdir_archive: Path = Path("/tmp/ai-agent-service/archives")
```

**Purpose**: Directory for archived session working directories

**Default**: `/tmp/ai-agent-service/archives`

**Customization**:
```bash
# .env
AGENT_WORKDIR_ARCHIVE=/data/archives
```

**Production Recommendation**:
- Use cheaper storage (HDD acceptable)
- Can be on different volume from active sessions
- Enable compression at filesystem level (if supported)
- Consider S3 for long-term retention

### Storage Quotas

**Session-Level Quota**:

From [config.py:56](../../app/core/config.py:56):
```python
max_working_dir_size_mb: int = 1024  # 1GB per session
```

**User-Level Quota** (future):
```python
# User model
max_total_storage_mb: int = 10240  # 10GB total across all sessions
```

**System-Level Monitoring**:
```python
async def check_system_storage():
    """Monitor overall storage usage."""
    import shutil

    # Check disk usage
    total, used, free = shutil.disk_usage(settings.agent_workdir_base)

    usage_percent = (used / total) * 100

    if usage_percent > 80:
        logger.warning(f"Disk usage at {usage_percent}%")
        await trigger_cleanup()
```

### Retention Policies

**Active Sessions**:

From [config.py:65](../../app/core/config.py:65):
```python
session_timeout_hours: int = 24  # Auto-terminate after 24h idle
```

**Completed Sessions**:

From [config.py:66](../../app/core/config.py:66):
```python
session_archive_days: int = 180  # Archive after 180 days
```

**Archives**:

From [config.py:118](../../app/core/config.py:118):
```python
archive_retention_days: int = 90  # Delete archives after 90 days
```

**Auto-Cleanup**:

From [config.py:117](../../app/core/config.py:117):
```python
archive_auto_cleanup: bool = True  # Enable automatic cleanup
```

---

## API Operations

### POST /api/v1/sessions/{id}/archive

**Archive Session Working Directory**

From [sessions.py:768-826](../../app/api/v1/sessions.py:768-826):

```python
@router.post("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def archive_session_endpoint(
    session_id: UUID,
    request: SessionArchiveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveMetadataResponse:
    """Archive session's working directory."""
```

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{id}/archive \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_to_s3": true
  }'
```

**Response**:
```json
{
  "id": "archive-uuid",
  "session_id": "session-uuid",
  "archive_path": "/archives/session-uuid_20251019_143022.tar.gz",
  "size_bytes": 52428800,
  "compression": "gzip",
  "status": "completed",
  "archived_at": "2025-10-19T14:30:22Z",
  "created_at": "2025-10-19T14:30:00Z"
}
```

### GET /api/v1/sessions/{id}/archive/download

**Download Archived Working Directory**

From [sessions.py:638-698](../../app/api/v1/sessions.py:638-698):

```python
@router.get("/{session_id}/workdir/download")
async def download_working_directory(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Download session working directory as tar.gz archive."""
```

**Request**:
```bash
curl -X GET http://localhost:8000/api/v1/sessions/{id}/workdir/download \
  -H "Authorization: Bearer TOKEN" \
  -o session-workdir.tar.gz
```

**Response**: Binary tar.gz stream

**Extract Archive**:
```bash
# Extract downloaded archive
tar -xzf session-workdir.tar.gz

# View contents
tar -tzf session-workdir.tar.gz
```

### DELETE /api/v1/sessions/{id}/archive

**Delete Archive** (future endpoint):

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/{id}/archive \
  -H "Authorization: Bearer TOKEN"
```

**Implementation**:
```python
@router.delete("/{session_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_archive(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete session archive."""

    # Get archive
    archive = await archive_repo.get_by_session(session_id)
    if not archive:
        raise HTTPException(404, "Archive not found")

    # Delete file
    Path(archive.archive_path).unlink(missing_ok=True)

    # Delete record
    await archive_repo.delete(archive.id)
    await db.commit()
```

---

## Common Tasks

### How to Increase Workdir Size Limit

**1. Update Configuration**:

```bash
# .env
MAX_WORKING_DIR_SIZE_MB=2048  # Increase to 2GB
```

**2. Restart Service**:
```bash
docker-compose restart ai-agent-api
```

**3. Verify**:
```python
from app.core.config import settings
print(settings.max_working_dir_size_mb)  # Should print 2048
```

**4. Apply to Existing Sessions** (optional):
```sql
-- Update quota for specific user
UPDATE users
SET max_working_dir_size_mb = 2048
WHERE id = 'user-uuid';
```

### How to Manually Trigger Archival

**Via API**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{id}/archive \
  -H "Authorization: Bearer TOKEN"
```

**Via Python**:
```python
from app.services.storage_manager import StorageManager

storage_manager = StorageManager()
archive_path = await storage_manager.archive_working_directory(session_id)

print(f"Archived to: {archive_path}")
```

**Via Admin CLI** (if exists):
```bash
python -m app.cli archive-session --session-id=<uuid>
```

### How to Restore from Archive

**Extract Archive Manually**:
```bash
# 1. Find archive
ls /tmp/ai-agent-service/archives/

# 2. Extract to temp location
mkdir /tmp/restore
tar -xzf /archives/session-uuid_timestamp.tar.gz -C /tmp/restore

# 3. Copy to new session workdir
cp -r /tmp/restore/session-uuid/* /sessions/new-session-uuid/
```

**Programmatic Restore**:
```python
async def restore_session_from_archive(
    archive_id: UUID,
    target_session_id: UUID
) -> Path:
    """Restore working directory from archive."""

    # Get archive metadata
    archive = await archive_repo.get_by_id(archive_id)

    # Create target directory
    target_dir = storage_manager.base_workdir / str(target_session_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract archive
    with tarfile.open(archive.archive_path, "r:gz") as tar:
        tar.extractall(target_dir)

    logger.info(f"Restored archive {archive_id} to {target_dir}")
    return target_dir
```

### How to Clean Up Old Archives

**Manual Cleanup**:
```bash
# Delete archives older than 90 days
find /tmp/ai-agent-service/archives/ -name "*.tar.gz" -mtime +90 -delete
```

**Using StorageManager**:
```python
from app.services.storage_manager import StorageManager

storage_manager = StorageManager()
deleted_count = await storage_manager.cleanup_old_archives(days=90)

print(f"Deleted {deleted_count} archives")
```

**Scheduled Cleanup** (Celery task):
```python
@celery.task
async def daily_archive_cleanup():
    """Clean up archives older than retention period."""
    storage_manager = StorageManager()

    deleted = await storage_manager.cleanup_old_archives(
        days=settings.archive_retention_days
    )

    logger.info(f"Daily cleanup: Deleted {deleted} expired archives")

    # Also clean up orphaned archives (no DB record)
    archive_repo = WorkingDirectoryArchiveRepository(db)
    all_archives = await archive_repo.get_all()
    archive_ids = {str(a.session_id) for a in all_archives}

    for archive_file in storage_manager.archive_dir.glob("*.tar.gz"):
        session_id = archive_file.stem.split("_")[0]
        if session_id not in archive_ids:
            archive_file.unlink()
            logger.info(f"Deleted orphaned archive: {archive_file}")
```

---

## Related Documentation

- **Session Lifecycle**: [SESSION_LIFECYCLE.md](SESSION_LIFECYCLE.md) - Working directory creation and cleanup
- **Session Modes**: [SESSION_MODES.md](SESSION_MODES.md) - How modes use working directories
- **Session Forking**: [SESSION_FORKING.md](SESSION_FORKING.md) - Working directory cloning
- **Storage Management**: [../../storage/STORAGE_MANAGER.md](../../storage/STORAGE_MANAGER.md) - Storage operations
- **Tool Integration**: [../../claude_sdk/TOOLS.md](../../claude_sdk/TOOLS.md) - How tools use working directories

---

## Related Files

**Services**:
- [storage_manager.py](../../app/services/storage_manager.py) - Complete implementation
- [session_service.py:76-78](../../app/services/session_service.py:76-78) - Working directory creation
- [session_service.py:226-227](../../app/services/session_service.py:226-227) - Archival on deletion

**Domain Models**:
- [working_directory.py](../../app/models/working_directory.py) - WorkingDirectory model
- [working_directory_archive.py](../../app/models/working_directory_archive.py) - Archive model
- [session.py:43](../../app/models/session.py:43) - working_directory_path field

**Repositories**:
- [working_directory_archive_repository.py](../../app/repositories/working_directory_archive_repository.py) - Archive data access

**API**:
- [sessions.py:638-698](../../app/api/v1/sessions.py:638-698) - Download endpoint
- [sessions.py:768-826](../../app/api/v1/sessions.py:768-826) - Archive endpoint
- [sessions.py:828-873](../../app/api/v1/sessions.py:828-873) - Get archive metadata

**Configuration**:
- [config.py:54-61](../../app/core/config.py:54-61) - Storage settings
- [config.py:110-118](../../app/core/config.py:110-118) - Archive settings

---

## Keywords

`working-directories`, `workdir`, `session-workspace`, `file-storage`, `storage-manager`, `directory-isolation`, `archival`, `compression`, `tar-gz`, `file-operations`, `tool-integration`, `read-tool`, `write-tool`, `bash-tool`, `storage-quotas`, `disk-space`, `archive-retention`, `s3-storage`, `filesystem-storage`, `session-files`, `working-directory-lifecycle`, `directory-cloning`, `path-resolution`, `security-isolation`

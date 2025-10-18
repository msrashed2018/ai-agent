# Reports Commands

Reports are generated from session outputs and can be exported in various formats (HTML, PDF, JSON, Markdown).

---

## Commands Overview

| CLI Command | API Endpoint | Description |
|------------|-------------|-------------|
| `ai-agent reports list` | `GET /api/v1/reports` | List all reports |
| `ai-agent reports get <report-id>` | `GET /api/v1/reports/{report_id}` | Get report details |
| `ai-agent reports download <report-id>` | `GET /api/v1/reports/{report_id}/download` | Download report file |

---

## 1. List Reports

### CLI Command
```bash
# List all reports
ai-agent reports list

# Filter by session
ai-agent reports list --session-id abc123

# Filter by type
ai-agent reports list --report-type task_execution

# With pagination
ai-agent reports list --page 1 --page-size 20

# JSON output
ai-agent reports list --output json
```

### What Happens in Backend API

**Step 1: Authentication**
```sql
-- Validate JWT token from Authorization header
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;
```

**Step 2: Query Reports**

If filtering by session ID:
```sql
-- Get reports for specific session
SELECT * FROM reports
WHERE session_id = 'session-uuid'
  AND deleted_at IS NULL
ORDER BY created_at DESC
OFFSET 0 LIMIT 100;
```

If listing all user's reports:
```sql
-- First, get all user's sessions
SELECT * FROM sessions
WHERE user_id = 'user-uuid'
  AND deleted_at IS NULL
OFFSET 0 LIMIT 1000;

-- Then, for each session, get reports
SELECT * FROM reports
WHERE session_id = 'session-uuid'
  AND deleted_at IS NULL
ORDER BY created_at DESC;
```

**Step 3: Apply Filters**

If `--report-type` provided, filter in memory:
```python
# Filter by report type
reports = [r for r in reports if r.report_type == report_type]
```

**Step 4: Build Response**

For each report, add HATEOAS links:
```json
{
  "id": "report-uuid",
  "session_id": "session-uuid",
  "title": "Task Execution Report",
  "report_type": "task_execution",
  "file_format": "html",
  "file_size_bytes": 15678,
  "created_at": "2025-01-15T10:30:00Z",
  "_links": {
    "self": "/api/v1/reports/report-uuid",
    "download_html": "/api/v1/reports/report-uuid/download?format=html",
    "download_pdf": "/api/v1/reports/report-uuid/download?format=pdf",
    "download_json": "/api/v1/reports/report-uuid/download?format=json",
    "session": "/api/v1/sessions/session-uuid"
  }
}
```

**Step 5: Return Paginated Response**
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 100,
  "pages": 1
}
```

### Key Backend Files
- Route handler: [app/api/v1/reports.py:75-138](../../ai-agent-api/app/api/v1/reports.py#L75-L138)
- Repository: [app/repositories/report_repository.py](../../ai-agent-api/app/repositories/report_repository.py)
- Database model: `reports` table

---

## 2. Get Report Details

### CLI Command
```bash
# Get report metadata
ai-agent reports get abc123

# JSON output
ai-agent reports get abc123 --output json
```

### What Happens in Backend API

**Step 1: Authentication**
```sql
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;
```

**Step 2: Fetch Report**
```sql
SELECT * FROM reports
WHERE id = 'report-uuid'
  AND deleted_at IS NULL;
```

**Step 3: Authorization Check**

Get associated session to verify ownership:
```sql
SELECT * FROM sessions
WHERE id = 'session-uuid';
```

Permission logic:
```python
# Check ownership
if session.user_id != current_user.id and current_user.role != "admin":
    raise HTTPException(403, "Not authorized to access this report")
```

**Step 4: Build Response with Links**
```json
{
  "id": "report-uuid",
  "session_id": "session-uuid",
  "user_id": "user-uuid",
  "title": "Kubernetes Health Check Report",
  "description": "Automated health check of production cluster",
  "report_type": "task_execution",
  "content": {
    "session_id": "session-uuid",
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": "Session execution summary",
    "sections": [],
    "metrics": {}
  },
  "file_path": "/data/reports/report-uuid.html",
  "file_format": "html",
  "file_size_bytes": 15678,
  "template_name": null,
  "tags": ["kubernetes", "health-check"],
  "task_execution_id": "execution-uuid",
  "is_public": false,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "_links": {
    "self": "/api/v1/reports/report-uuid",
    "download_html": "/api/v1/reports/report-uuid/download?format=html",
    "download_pdf": "/api/v1/reports/report-uuid/download?format=pdf",
    "download_json": "/api/v1/reports/report-uuid/download?format=json",
    "session": "/api/v1/sessions/session-uuid"
  }
}
```

### Key Backend Files
- Route handler: [app/api/v1/reports.py:31-72](../../ai-agent-api/app/api/v1/reports.py#L31-L72)
- Repository: [app/repositories/report_repository.py:17-27](../../ai-agent-api/app/repositories/report_repository.py#L17-L27)

---

## 3. Download Report File

### CLI Command
```bash
# Download as HTML (default)
ai-agent reports download abc123

# Download as PDF
ai-agent reports download abc123 --format pdf

# Download as JSON
ai-agent reports download abc123 --format json

# Save to specific file
ai-agent reports download abc123 --output report.html
```

### What Happens in Backend API

**Step 1: Authentication & Authorization**
```sql
-- Validate user
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;

-- Get report
SELECT * FROM reports
WHERE id = 'report-uuid'
  AND deleted_at IS NULL;

-- Get session for ownership check
SELECT * FROM sessions WHERE id = 'session-uuid';
```

Authorization check:
```python
if session.user_id != current_user.id and current_user.role != "admin":
    raise HTTPException(403, "Not authorized to access this report")
```

**Step 2: Validate Format**
```python
# Only html, pdf, json allowed
if format not in ["html", "pdf", "json"]:
    raise HTTPException(400, "Invalid format. Must be html, pdf, or json")
```

**Step 3: Get File Path**

Reports are stored in: `/data/reports/{report_id}.{format}`

```python
# Check if file exists
file_path = settings.reports_dir / f"{report_id}.{format}"
if not file_path.exists():
    raise HTTPException(404, "Report file not found in {format} format")
```

**Step 4: Stream File to Client**

File is streamed using FastAPI's FileResponse:
```python
media_types = {
    "html": "text/html",
    "pdf": "application/pdf",
    "json": "application/json",
}

return FileResponse(
    path=file_path,
    media_type=media_types[format],
    filename=f"{report_id}.{format}",
)
```

### Report Generation Flow (From Task Execution)

When a task execution completes with `generate_report: true`, the following happens:

**Step 1: Build Report Content**

Query session data:
```sql
-- Get session messages
SELECT * FROM messages
WHERE session_id = 'session-uuid'
ORDER BY created_at ASC;

-- Get tool calls
SELECT * FROM tool_calls
WHERE session_id = 'session-uuid'
ORDER BY created_at ASC;
```

Build content structure (currently simplified):
```python
content = {
    "session_id": str(session_id),
    "generated_at": datetime.utcnow().isoformat(),
    "summary": "Session execution summary",
    "sections": [],  # TODO: Add message sections
    "metrics": {},   # TODO: Add execution metrics
}
```

**Step 2: Format Report**

Depending on format:

**JSON Format:**
```python
import json
file_content = json.dumps(content, indent=2)
```

**Markdown Format:**
```python
md = f"# {content.get('summary', 'Report')}\n\n"
md += f"Generated at: {content.get('generated_at')}\n\n"
# ... add more sections
file_content = md
```

**HTML Format:**
```python
html = f"<html><body>"
html += f"<h1>{content.get('summary', 'Report')}</h1>"
html += f"<p>Generated at: {content.get('generated_at')}</p>"
# ... add more sections
html += "</body></html>"
file_content = html
```

**PDF Format (Future):**
```python
# TODO: Use library like WeasyPrint or ReportLab
# Convert HTML to PDF
from weasyprint import HTML
pdf_bytes = HTML(string=html_content).write_pdf()
```

**Step 3: Save to Filesystem**

```python
# Create reports directory if not exists
reports_dir = Path("/data/reports")
reports_dir.mkdir(parents=True, exist_ok=True)

# Write file
file_path = reports_dir / f"{report_id}.{format}"

if format == "pdf":
    # Binary write for PDF
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
else:
    # Text write for HTML/JSON/Markdown
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

file_size = file_path.stat().st_size
```

**Step 4: Update Database**

```sql
INSERT INTO reports (
  id, session_id, user_id, title, description,
  report_type, content, file_path, file_format, file_size_bytes,
  tags, is_public, created_at, updated_at
) VALUES (
  'report-uuid',
  'session-uuid',
  'user-uuid',
  'Task Execution Report',
  'Automated report from task execution',
  'task_execution',
  '{"session_id": "...", "summary": "..."}',
  '/data/reports/report-uuid.html',
  'html',
  15678,
  ARRAY['kubernetes', 'health-check'],
  false,
  '2025-01-15T10:30:00Z',
  '2025-01-15T10:30:00Z'
);
```

**Step 5: Audit Log**
```sql
INSERT INTO audit_logs (
  id, user_id, action, resource_type, resource_id,
  details, created_at
) VALUES (
  'audit-uuid',
  'user-uuid',
  'report_generated',
  'report',
  'report-uuid',
  '{"report_type": "task_execution", "session_id": "session-uuid"}',
  '2025-01-15T10:30:00Z'
);
```

### Complete Flow Diagram

```
CLI Command: ai-agent reports download abc123 --format pdf
    ↓
HTTP Request: GET /api/v1/reports/abc123/download?format=pdf
    ↓
API Route Handler (reports.py:141-203)
    ↓
    ├─→ Authenticate User (JWT token)
    ├─→ Query Report from Database
    ├─→ Check Authorization (session ownership)
    ├─→ Validate Format (html/pdf/json)
    ├─→ Get File Path (/data/reports/abc123.pdf)
    └─→ Stream File with FileResponse
         ↓
         media_type: "application/pdf"
         filename: "abc123.pdf"
         ↓
CLI receives file and saves to disk
```

### Key Backend Files
- Route handler: [app/api/v1/reports.py:141-203](../../ai-agent-api/app/api/v1/reports.py#L141-L203)
- Report service: [app/services/report_service.py](../../ai-agent-api/app/services/report_service.py)
- Storage manager: [app/services/storage_manager.py:109-156](../../ai-agent-api/app/services/storage_manager.py#L109-L156)
- Report formatting: [app/services/report_service.py:270-294](../../ai-agent-api/app/services/report_service.py#L270-L294)

---

## Report Types

| Type | Description | When Generated |
|------|-------------|----------------|
| `task_execution` | Generated from automated task execution | When task runs with `generate_report: true` |
| `manual` | Manually generated from session | User explicitly generates report from session |
| `scheduled` | Generated on schedule | Future: Scheduled report generation |
| `auto_generated` | Automatically generated | Default type for system-generated reports |

---

## Report Formats

| Format | Media Type | Use Case |
|--------|-----------|----------|
| `html` | `text/html` | Web viewing, default format |
| `pdf` | `application/pdf` | Printable reports, archival |
| `json` | `application/json` | Machine-readable, data export |
| `markdown` | `text/markdown` | Developer-friendly, version control |

---

## Storage Locations

- **Reports Directory**: `/data/reports/`
- **File Naming**: `{report_id}.{format}` (e.g., `abc123.html`)
- **Database Records**: `reports` table with metadata
- **File Management**: Handled by `StorageManager` service

---

## Examples

### Example 1: List and Download Report

```bash
# List reports for a session
ai-agent reports list --session-id abc123 --output json

# Response shows available reports
{
  "items": [
    {
      "id": "report-001",
      "title": "Health Check Report",
      "file_format": "html",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}

# Download the HTML report
ai-agent reports download report-001 --output health-check.html

# Download as PDF
ai-agent reports download report-001 --format pdf --output health-check.pdf
```

### Example 2: Task Execution with Report

```bash
# Execute task with report generation
ai-agent tasks execute task-001 \
  --generate-report \
  --report-format html \
  --wait

# Response includes report_id
{
  "execution_id": "exec-001",
  "status": "completed",
  "report_id": "report-002"
}

# Get report details
ai-agent reports get report-002

# Download the report
ai-agent reports download report-002
```

---

## Notes

- **Authorization**: Users can only access reports from their own sessions (unless admin)
- **Soft Delete**: Reports are soft-deleted (marked with `deleted_at` timestamp)
- **File Persistence**: Report files persist even if database record is deleted (until cleanup)
- **Format Conversion**: Currently only one format per report; future versions may support multi-format
- **Content Structure**: Report content format is currently simplified; future versions will include detailed message logs, tool call summaries, and execution metrics

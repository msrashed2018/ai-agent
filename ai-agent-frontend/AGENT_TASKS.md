# Agent Task Definitions

## Overview
This document contains detailed task definitions for 9 specialized agents to work in parallel on the AI Agent Frontend implementation. Each agent has specific responsibilities and clear deliverables.

---

## 🔧 Agent 1: Foundation Agent

### Responsibility
Set up the foundational components, utilities, and shared UI elements that all other agents will depend on.

### Context
- **OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`
- **Existing Files**:
  - `src/types/api.ts` (all TypeScript types)
  - `src/lib/api-client.ts` (API client)
  - `src/lib/utils.ts` (utility functions)
  - `src/lib/auth.ts` (auth service)

### Tasks

#### 1. Install shadcn/ui Components
```bash
cd /workspace/me/repositories/kubemind/ai-agent-frontend

# Initialize shadcn/ui (if not done)
npx shadcn-ui@latest init

# Install all required components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add table
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add popover
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add progress
```

#### 2. Create Custom UI Components (`src/components/ui/`)

**StatusBadge.tsx**
```typescript
// Display status with color coding
// Props: status (string), variant (success|warning|error|info)
// Use getStatusColor from utils.ts
```

**EmptyState.tsx**
```typescript
// Empty state with icon, message, and optional CTA button
// Props: icon, title, description, action (optional)
```

**LoadingState.tsx**
```typescript
// Loading skeleton for different content types
// Props: type (card|table|list|detail)
```

**PageHeader.tsx**
```typescript
// Consistent page header with title, description, actions
// Props: title, description, actions (ReactNode)
```

**MetricCard.tsx**
```typescript
// Dashboard metric card with number, label, trend
// Props: value, label, icon, trend (optional)
```

**ConfirmDialog.tsx**
```typescript
// Reusable confirmation dialog for destructive actions
// Props: open, onOpenChange, onConfirm, title, description
```

**CodeBlock.tsx**
```typescript
// Display code/JSON with syntax highlighting
// Props: code (string), language (json|bash|typescript)
// Use a lightweight syntax highlighter or just format JSON
```

#### 3. Create Custom Hooks (`src/hooks/`)

**useToast.ts**
```typescript
// Wrapper around Sonner toast
// Export: useToast hook with toast.success, toast.error, toast.info
```

**useDebounce.ts**
```typescript
// Debounce hook for search inputs
// Takes value and delay, returns debounced value
```

**useMediaQuery.ts**
```typescript
// Media query hook for responsive design
// Takes query string, returns boolean
```

**useConfirm.ts**
```typescript
// Confirmation dialog hook
// Returns confirm function that shows dialog
```

**useCopyToClipboard.ts**
```typescript
// Copy to clipboard with feedback
// Returns copy function and copied state
```

#### 4. Create Providers (`src/app/providers.tsx`)
Already exists, but ensure it's complete with React Query devtools

#### 5. Create Protected Route Wrapper (`src/components/auth/`)

**ProtectedRoute.tsx**
```typescript
// Wrapper that redirects to login if not authenticated
// Check useAuthStore for isAuthenticated
// Show loading while checking
```

**AdminRoute.tsx**
```typescript
// Wrapper that checks for admin role
// Redirect to home if not admin
```

### Deliverables
- [ ] All shadcn/ui components installed
- [ ] 7 custom UI components created
- [ ] 5 custom hooks created
- [ ] Protected route wrappers created
- [ ] All components follow TypeScript strict mode
- [ ] All components are accessible (ARIA labels)

---

## 🎨 Agent 2: Layout Agent

### Responsibility
Create the main application layout structure including header, sidebar, and navigation.

### Dependencies
- Foundation Agent must complete first

### Context
- **Design**: Modern sidebar layout with collapsible navigation
- **Navigation Structure**:
  - Home (/)
  - Sessions (/sessions)
  - Tasks (/tasks)
  - MCP Servers (/mcp-servers)
  - Reports (/reports)
  - Admin (/admin) - admin only

### Tasks

#### 1. Create Main Layout (`src/components/layout/`)

**AppLayout.tsx**
```typescript
// Main layout with sidebar and content area
// Props: children
// Structure: Sidebar on left, content on right
// Responsive: Collapse sidebar on mobile
```

**Header.tsx**
```typescript
// Top header with:
// - Logo/brand on left
// - Search bar in center (future feature)
// - User menu on right
// Props: user (from useAuthStore)
// Include notifications icon (future)
```

**Sidebar.tsx**
```typescript
// Left sidebar with navigation
// Navigation items from navigation config
// Icons from lucide-react
// Active state highlighting
// Collapsible on mobile
// Admin section at bottom (if admin)
```

**UserMenu.tsx**
```typescript
// Dropdown menu from Header
// Items: Profile, Settings, Logout
// Use DropdownMenu from shadcn/ui
// Include user avatar and name
```

**Breadcrumb.tsx**
```typescript
// Breadcrumb navigation
// Auto-generate from route path
// Props: items (array of {label, href})
```

#### 2. Create Navigation Config (`src/lib/navigation.ts`)

```typescript
// Define navigation structure
// Each item: { label, href, icon, adminOnly }
// Export as const for type safety
```

#### 3. Update Root Layout (`src/app/layout.tsx`)

```typescript
// Wrap children with Providers
// Include Toaster from Sonner
// Include AppLayout for authenticated routes
```

#### 4. Create Page Wrapper (`src/components/layout/PageContainer.tsx`)

```typescript
// Consistent page padding and max-width
// Props: children, className
```

### Deliverables
- [ ] AppLayout with sidebar and content area
- [ ] Header with user menu
- [ ] Sidebar with navigation
- [ ] Breadcrumb component
- [ ] Navigation config
- [ ] Responsive design (mobile collapsible)
- [ ] Active route highlighting

---

## 🔐 Agent 3: Auth Agent

### Responsibility
Implement authentication pages and flows.

### Dependencies
- Foundation Agent
- Layout Agent

### Context
- **API Endpoints**:
  - POST `/api/v1/auth/login` - Login with email/password
  - GET `/api/v1/auth/me` - Get current user
  - POST `/api/v1/auth/refresh` - Refresh token
- **Schemas**: LoginRequest, LoginResponse in `src/types/api.ts`

### Tasks

#### 1. Create Login Page (`src/app/auth/login/page.tsx`)

```typescript
// Login form with:
// - Email input (validated)
// - Password input (validated)
// - Login button
// - Error display
// - Loading state
// Use React Hook Form + Zod
// On success: store tokens, set user, redirect to /
// Handle errors: show toast
```

#### 2. Create Login Form (`src/components/auth/LoginForm.tsx`)

```typescript
// Reusable login form component
// Props: onSuccess callback
// Validation schema with Zod
// Use useForm from react-hook-form
// Call apiClient.login()
```

#### 3. Create Auth Guard (`src/components/auth/AuthGuard.tsx`)

```typescript
// Component that checks auth on mount
// If not authenticated, redirect to /auth/login
// Show loading while checking
// Use useAuthStore
```

#### 4. Update Root Page (`src/app/page.tsx`)

```typescript
// Wrap with AuthGuard
// Redirect to appropriate page based on role
```

#### 5. Create Logout Function (in UserMenu)

```typescript
// Logout button in UserMenu
// Call apiClient.logout()
// Clear auth store
// Redirect to /auth/login
```

### Deliverables
- [ ] Login page with form
- [ ] Form validation (email, password required)
- [ ] Loading and error states
- [ ] Auto-redirect if authenticated
- [ ] Logout functionality in UserMenu
- [ ] Auth guard for protected routes

---

## 📊 Agent 4: Dashboard Agent

### Responsibility
Create the main dashboard/home page with overview statistics and recent activity.

### Dependencies
- Foundation Agent
- Layout Agent
- Auth Agent

### Context
- **API Endpoints**:
  - GET `/api/v1/sessions` - Recent sessions
  - GET `/api/v1/tasks/executions/*` - Recent executions
  - GET `/api/v1/admin/stats` - System stats (if admin)

### Tasks

#### 1. Create Dashboard Page (`src/app/page.tsx`)

```typescript
// Dashboard with:
// - Welcome header with user name
// - Stats cards row (sessions, tasks, cost)
// - Recent sessions table
// - Recent task executions table
// - Quick action buttons
// Use MetricCard component
```

#### 2. Create Stats Cards Section

```typescript
// 4 cards:
// - Total Sessions (with active count)
// - Total Tasks (with scheduled count)
// - Total Cost (formatted currency)
// - Recent Activity (count today)
// Use MetricCard from foundation
```

#### 3. Create Recent Activity Section

```typescript
// Two tables side by side:
// - Recent Sessions (last 5)
// - Recent Executions (last 5)
// Link to full lists
// Show status badges
```

#### 4. Create Quick Actions Section

```typescript
// Large buttons for:
// - Create New Session
// - Create New Task
// - View All Sessions
// - View All Tasks
```

#### 5. Create Data Hooks (`src/hooks/useDashboard.ts`)

```typescript
// Combine multiple queries:
// - useRecentSessions
// - useRecentExecutions
// - useStats (if admin)
```

### Deliverables
- [ ] Dashboard page with stats
- [ ] Stats cards (responsive grid)
- [ ] Recent activity tables
- [ ] Quick actions
- [ ] Loading skeletons
- [ ] Error states
- [ ] Refresh button

---

## 💬 Agent 5: Sessions Agent

### Responsibility
Implement all session-related pages and components.

### Dependencies
- Foundation Agent
- Layout Agent
- Auth Agent

### Context
- **API Endpoints**: Review OpenAPI schema for `/api/v1/sessions/*` endpoints
- **Key Features**: List, create, query (chat interface), pause, resume, messages, tool calls

### Tasks

#### 1. Create Sessions List Page (`src/app/sessions/page.tsx`)

```typescript
// Table with columns:
// - Name, Status, Model, Messages, Tool Calls, Cost, Created
// Features:
// - Search by name
// - Filter by status (dropdown)
// - Sort by any column
// - Pagination
// - Create button (opens dialog)
// - Quick actions menu (view, query, pause, delete)
```

#### 2. Create Session Create Dialog (`src/components/sessions/CreateSessionDialog.tsx`)

```typescript
// Form fields:
// - Name (optional)
// - Description (optional, textarea)
// - Model (select with common models)
// - Allowed Tools (multi-select)
// - System Prompt (textarea, optional)
// - MCP Servers (multi-select, fetch from API)
// Form validation with Zod
// On success: redirect to session detail
```

#### 3. Create Session Detail Page (`src/app/sessions/[sessionId]/page.tsx`)

```typescript
// Layout:
// - Top: Session info card (name, status, model, dates)
// - Stats row: messages, tool calls, cost
// - Action buttons: Query, Pause/Resume, Download Workdir
// - Tabs: Overview, Messages, Tool Calls, Configuration
// Overview tab: Display SDK options, working directory
// Messages tab: List of messages with role badges
// Tool Calls tab: Timeline of tool calls with expand/collapse
// Configuration tab: Allowed tools, MCP servers
```

#### 4. Create Query Interface Page (`src/app/sessions/[sessionId]/query/page.tsx`)

```typescript
// Chat interface:
// - Message history (scrollable, auto-scroll to bottom)
// - User messages (right, blue bubble)
// - Assistant messages (left, gray bubble)
// - Input area at bottom (textarea + send button)
// - Loading indicator during response
// - Tool call indicators in timeline
// - Copy message button on hover
```

#### 5. Create Session Components

**SessionTable.tsx**
```typescript
// Reusable sessions table with sorting/filtering
```

**SessionCard.tsx**
```typescript
// Card view for sessions (grid alternative to table)
```

**MessageBubble.tsx**
```typescript
// Chat message display with role-based styling
```

**ToolCallCard.tsx**
```typescript
// Expandable card showing tool call details
```

#### 6. Create Session Hooks (`src/hooks/useSessions.ts`)

```typescript
// useSessions - list sessions
// useSession - get single session
// useCreateSession - create mutation
// useQuerySession - send message mutation
// usePauseSession - pause mutation
// useResumeSession - resume mutation
// useSessionMessages - get messages
// useSessionToolCalls - get tool calls
```

### Deliverables
- [ ] Sessions list page with table
- [ ] Create session dialog
- [ ] Session detail page with tabs
- [ ] Query interface (chat)
- [ ] Messages viewer
- [ ] Tool calls viewer
- [ ] All session hooks
- [ ] Pause/resume functionality
- [ ] Download workdir button

---

## ⚙️ Agent 6: Tasks Agent

### Responsibility
Implement all task automation pages and components.

### Dependencies
- Foundation Agent
- Layout Agent
- Auth Agent

### Context
- **API Endpoints**: Review OpenAPI schema for `/api/v1/tasks/*` endpoints
- **Key Features**: List, create, edit, delete, execute, view executions

### Tasks

#### 1. Create Tasks List Page (`src/app/tasks/page.tsx`)

```typescript
// Table with columns:
// - Name, Schedule, Enabled, Success/Fail Counts, Last Run, Next Run
// Features:
// - Search by name/tags
// - Filter by scheduled/manual
// - Filter by enabled/disabled
// - Sort by columns
// - Pagination
// - Create button
// - Quick actions (execute, edit, toggle enable, delete)
```

#### 2. Create Task Form Page (`src/app/tasks/new/page.tsx` and `src/app/tasks/[taskId]/edit/page.tsx`)

```typescript
// Form fields:
// - Name (required)
// - Description (optional, textarea)
// - Prompt Template (required, textarea with syntax highlighting)
// - Template Variables (key-value editor)
// - Schedule toggle
// - Cron expression (if scheduled, with validation)
// - Report generation toggle
// - Report format (select: html, pdf, json, markdown)
// - Tags (chip input)
// Form validation
// Preview section showing rendered prompt
```

#### 3. Create Task Detail Page (`src/app/tasks/[taskId]/page.tsx`)

```typescript
// Layout:
// - Task info card (name, description, schedule)
// - Execution stats (success/fail counts, avg duration)
// - Action buttons (Execute, Edit, Delete, Toggle Enable)
// - Template preview (with variables highlighted)
// - Tags display
// - Execution history table (paginated)
```

#### 4. Create Execute Task Dialog (`src/components/tasks/ExecuteTaskDialog.tsx`)

```typescript
// Modal with:
// - Variable inputs (pre-filled with defaults from task)
// - Validation before execution
// - Execute button
// - Progress indicator
// - On success: show execution ID, link to detail
```

#### 5. Create Execution Detail Page (`src/app/tasks/executions/[executionId]/page.tsx`)

```typescript
// Show:
// - Execution info (status, times, variables used)
// - Link to task
// - Link to session
// - Link to report (if generated)
// - Error message (if failed)
// - Re-run button
```

#### 6. Create Task Components

**TaskTable.tsx**
```typescript
// Reusable tasks table
```

**TemplateEditor.tsx**
```typescript
// Textarea with variable syntax highlighting
// Variable list below with add/remove
```

**CronBuilder.tsx**
```typescript
// Helper to build cron expressions visually
// Or just show next runs preview
```

**ExecutionTable.tsx**
```typescript
// Table of task executions
```

#### 7. Create Task Hooks (`src/hooks/useTasks.ts`)

```typescript
// useTasks - list tasks
// useTask - get single task
// useCreateTask - create mutation
// useUpdateTask - update mutation
// useDeleteTask - delete mutation
// useExecuteTask - execute mutation
// useTaskExecutions - list executions
// useTaskExecution - get single execution
```

### Deliverables
- [ ] Tasks list page with table
- [ ] Task create/edit form
- [ ] Task detail page
- [ ] Execute task dialog
- [ ] Execution detail page
- [ ] Execution history table
- [ ] Template editor with variables
- [ ] All task hooks
- [ ] Cron validation
- [ ] Re-run functionality

---

## 🔌 Agent 7: MCP Agent

### Responsibility
Implement MCP server management pages and components.

### Dependencies
- Foundation Agent
- Layout Agent
- Auth Agent

### Context
- **API Endpoints**: Review OpenAPI schema for `/api/v1/mcp-servers/*` endpoints
- **Key Features**: List, create, import/export, templates, health check
- **Server Types**: stdio, sse, http (different config schemas)

### Tasks

#### 1. Create MCP Servers List Page (`src/app/mcp-servers/page.tsx`)

```typescript
// Card grid view (better than table for complex configs):
// Each card shows:
// - Server name and type badge
// - Description
// - Health status indicator
// - Global/user badge
// - Enabled toggle
// - Quick actions (edit, health check, delete)
// Features:
// - Search by name
// - Filter by type
// - Filter by health status
// - Create button
// - Import config button
// - Export config button
```

#### 2. Create MCP Server Form Dialog (`src/components/mcp/ServerFormDialog.tsx`)

```typescript
// Multi-step form:
// Step 1: Select server type (stdio, sse, http)
// Step 2: Type-specific configuration
//   stdio: command, args array, env variables (key-value)
//   sse: URL, headers (key-value)
//   http: URL, headers (key-value)
// Step 3: Name, description, enable toggle
// Validation per type
// Test connection button (before save)
```

#### 3. Create Import Dialog (`src/components/mcp/ImportConfigDialog.tsx`)

```typescript
// File upload:
// - Drag and drop zone
// - File input for JSON
// - Validation (must be valid JSON)
// - Preview: show servers found
// - Override existing checkbox
// - Import button
// - Success summary (imported, skipped, errors)
```

#### 4. Create Export Dialog (`src/components/mcp/ExportConfigDialog.tsx`)

```typescript
// Options:
// - Include global servers checkbox
// - Download button
// - Copy to clipboard button
// - Success feedback
```

#### 5. Create Templates Page (`src/app/mcp-servers/templates/page.tsx`)

```typescript
// Grid of template cards:
// - Template name and icon
// - Description
// - Required configuration preview
// - Create from template button
// Popular templates highlighted
// Opens create dialog with pre-filled values
```

#### 6. Create MCP Components

**ServerCard.tsx**
```typescript
// Display server info in card format
// Shows all config in expandable section
```

**ServerConfigForm.tsx**
```typescript
// Dynamic form based on server type
```

**HealthBadge.tsx**
```typescript
// Health status indicator with icon
```

**KeyValueEditor.tsx**
```typescript
// Component for editing key-value pairs (env, headers)
```

#### 7. Create MCP Hooks (`src/hooks/useMCPServers.ts`)

```typescript
// useMCPServers - list servers
// useMCPServer - get single server
// useCreateMCPServer - create mutation
// useUpdateMCPServer - update mutation
// useDeleteMCPServer - delete mutation
// useHealthCheckMCPServer - health check mutation
// useMCPTemplates - get templates
// useImportMCPConfig - import mutation (file upload)
// useExportMCPConfig - export query
```

### Deliverables
- [ ] MCP servers list (card grid)
- [ ] Server create form (type-specific)
- [ ] Import dialog with file upload
- [ ] Export dialog
- [ ] Templates browser
- [ ] Health check functionality
- [ ] Server detail/edit
- [ ] All MCP hooks
- [ ] Type validation by server type

---

## 📄 Agent 8: Reports Agent

### Responsibility
Implement reports listing and viewing pages.

### Dependencies
- Foundation Agent
- Layout Agent
- Auth Agent

### Context
- **API Endpoints**: Review OpenAPI schema for `/api/v1/reports/*` endpoints
- **Key Features**: List, view, download (multiple formats)
- **Formats**: HTML, PDF, JSON, Markdown

### Tasks

#### 1. Create Reports List Page (`src/app/reports/page.tsx`)

```typescript
// Table with columns:
// - Title, Type, Format, File Size, Created, Actions
// Features:
// - Search by title
// - Filter by type (task_execution, manual, etc.)
// - Filter by format
// - Filter by session
// - Sort by columns
// - Pagination
// - Quick actions (view, download)
```

#### 2. Create Report Viewer Page (`src/app/reports/[reportId]/page.tsx`)

```typescript
// Layout:
// - Report info card (title, type, format, size, dates)
// - Download buttons row (HTML, PDF, JSON, Markdown)
// - Content preview:
//   - HTML: render in iframe
//   - JSON: syntax highlighted JSON viewer
//   - Markdown: rendered markdown
//   - PDF: show download button only
// - Link to session
// - Link to task execution (if applicable)
// - Tags display
```

#### 3. Create Report Components

**ReportTable.tsx**
```typescript
// Reusable reports table
```

**ReportViewer.tsx**
```typescript
// Display report content based on format
```

**DownloadButton.tsx**
```typescript
// Download report in specific format
// Show progress during download
```

#### 4. Create Download Functionality

```typescript
// Handle file downloads:
// - Call apiClient.downloadReport(id, format)
// - Convert blob to file
// - Trigger browser download
// - Show success toast
```

#### 5. Create Report Hooks (`src/hooks/useReports.ts`)

```typescript
// useReports - list reports (with filters)
// useReport - get single report
// useDownloadReport - download mutation
```

### Deliverables
- [ ] Reports list page
- [ ] Report viewer page
- [ ] Download functionality (all formats)
- [ ] Content preview (HTML, JSON, Markdown)
- [ ] Filter by type, format, session
- [ ] All report hooks
- [ ] Format-specific rendering

---

## 👑 Agent 9: Admin Agent

### Responsibility
Implement admin dashboard and management pages.

### Dependencies
- Foundation Agent
- Layout Agent
- Auth Agent

### Context
- **API Endpoints**: Review OpenAPI schema for `/api/v1/admin/*` endpoints
- **Access**: Admin role only
- **Key Features**: System stats, all sessions view, all users view

### Tasks

#### 1. Create Admin Dashboard Page (`src/app/admin/page.tsx`)

```typescript
// Layout:
// - Large stats cards (sessions, tasks, users, cost)
// - Charts:
//   - Sessions over time (last 30 days)
//   - Cost breakdown chart
//   - Storage usage pie chart
// - Recent activity across all users
// - Quick links to detailed views
```

#### 2. Create System Stats Section

```typescript
// Metric cards:
// - Total Sessions (with active/completed breakdown)
// - Total Tasks (with scheduled count)
// - Total Users (with active count)
// - Total Cost (with today's cost)
// - Storage Usage (working dirs, reports, archives)
// All with trend indicators
```

#### 3. Create All Sessions Page (`src/app/admin/sessions/page.tsx`)

```typescript
// Table with ALL sessions (all users):
// - Columns: User, Name, Status, Model, Messages, Cost, Created
// - User avatar and email in user column
// - Filter by user (searchable dropdown)
// - Filter by status
// - Search by session name
// - Sort by all columns
// - Pagination
// - View session link
```

#### 4. Create All Users Page (`src/app/admin/users/page.tsx`)

```typescript
// Table with all users:
// - Columns: Email, Role, Sessions Count, Tasks Count, Created, Active
// - Role badges
// - Active status indicator
// - Session/task counts (linked)
// - Filter by role
// - Include deleted toggle
// - Search by email
// - Sort by columns
```

#### 5. Create Admin Components

**StatsCard.tsx**
```typescript
// Large metric card with trend
```

**ActivityChart.tsx**
```typescript
// Simple line/bar chart for activity
// Can use a lightweight chart library or CSS bars
```

**CostChart.tsx**
```typescript
// Cost visualization over time
```

#### 6. Create Admin Hooks (`src/hooks/useAdmin.ts`)

```typescript
// useSystemStats - get system stats
// useAllSessions - list all sessions (with filters)
// useAllUsers - list all users (with filters)
```

#### 7. Add Admin Route Guard

```typescript
// Wrap admin pages with AdminRoute component
// Redirect to home if not admin
```

### Deliverables
- [ ] Admin dashboard with stats
- [ ] All sessions view (cross-user)
- [ ] All users view
- [ ] Charts and visualizations
- [ ] Admin route guard
- [ ] Filter by user functionality
- [ ] All admin hooks
- [ ] Role-based access control

---

## 🚀 Execution Strategy

### Parallel Execution Groups

**Group 1** (Start Immediately):
- Agent 1: Foundation Agent

**Group 2** (After Group 1 completes):
- Agent 2: Layout Agent
- Agent 3: Auth Agent (partially independent)

**Group 3** (After Group 2 completes):
- Agent 4: Dashboard Agent
- Agent 5: Sessions Agent
- Agent 6: Tasks Agent
- Agent 7: MCP Agent
- Agent 8: Reports Agent
- Agent 9: Admin Agent

### Estimated Timeline
- Group 1: 2-3 hours
- Group 2: 1-2 hours each
- Group 3: 2-4 hours each (parallel)

**Total Time**: 4-8 hours for complete implementation (with 6 agents running in parallel for Group 3)

---

## ✅ Quality Checklist for All Agents

### Code Quality
- [ ] TypeScript strict mode, no `any` types
- [ ] Proper error handling (try-catch)
- [ ] Loading states for all async operations
- [ ] Error states with user-friendly messages
- [ ] Success feedback (toasts)
- [ ] Form validation where applicable
- [ ] Accessible components (ARIA labels, keyboard navigation)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Consistent spacing (use Tailwind classes)
- [ ] Consistent naming (follow conventions)

### React Query Best Practices
- [ ] Use proper query keys (array format)
- [ ] Set appropriate stale times
- [ ] Invalidate queries after mutations
- [ ] Handle loading and error states
- [ ] Use optimistic updates where applicable

### Component Structure
- [ ] Small, focused components
- [ ] Proper prop types (TypeScript interfaces)
- [ ] Named exports
- [ ] JSDoc comments for complex logic
- [ ] Separate concerns (UI vs logic)

### Testing Readiness
- [ ] Components accept testable props
- [ ] Business logic in hooks (testable)
- [ ] Mock-friendly API calls
- [ ] Data-testid attributes on key elements

---

## 📝 Agent Communication Protocol

### If You Get Stuck
1. Check OpenAPI schema: `curl http://localhost:8000/api/v1/openapi.json | jq '.paths."/your/endpoint"'`
2. Check existing types: `cat src/types/api.ts | grep YourType`
3. Check API client: `cat src/lib/api-client.ts | grep yourMethod`

### File Naming Conventions
- Pages: `page.tsx` (Next.js App Router)
- Components: `ComponentName.tsx` (PascalCase)
- Hooks: `useHookName.ts` (camelCase with 'use')
- Utils: `util-name.ts` (kebab-case)

### Import Order
1. React/Next imports
2. Third-party imports
3. Local imports (@/ paths)
4. Relative imports
5. Type imports (at the end)

---

## 🎯 Success Criteria

### When You're Done
- [ ] All pages render without errors
- [ ] All API calls work correctly
- [ ] Loading states show during fetches
- [ ] Error messages display on failures
- [ ] Success toasts show on mutations
- [ ] Forms validate correctly
- [ ] Responsive on all screen sizes
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] Follows code patterns from foundation files

**Good luck! 🚀**

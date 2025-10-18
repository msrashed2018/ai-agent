# Layout Components

This directory contains the main application layout components that provide a consistent navigation and layout structure across all pages.

## Components

### AppLayout

Main application layout component that combines the sidebar and header.

**Location**: `src/components/layout/app-layout.tsx`

**Props**:
- `children: React.ReactNode` - Page content
- `title?: string` - Optional page title to display in header

**Features**:
- Two-column layout with fixed sidebar and scrollable content area
- Responsive design with mobile hamburger menu
- Manages sidebar open/close state
- Provides consistent spacing and styling

**Usage**:
```tsx
import { AppLayout } from '@/components/layout';

export default function MyPage() {
  return (
    <AppLayout title="My Page">
      <div>Page content here</div>
    </AppLayout>
  );
}
```

### Sidebar

Navigation sidebar component with menu items and user section.

**Location**: `src/components/layout/sidebar.tsx`

**Props**:
- `isOpen?: boolean` - Controls sidebar visibility
- `onClose?: () => void` - Callback when sidebar should close (mobile)

**Features**:
- Fixed width (260px) on desktop
- Full-screen overlay on mobile
- Logo/brand at top
- Navigation menu with active state highlighting
- User info section at bottom
- Admin-only menu items (filtered based on user role)
- Smooth transitions

**Navigation Items**:
- Dashboard (/)
- Sessions (/sessions)
- Tasks (/tasks)
- MCP Servers (/mcp-servers)
- Reports (/reports)
- Admin (/admin) - Only visible to admins

### Header

Top header bar component with hamburger menu and user menu.

**Location**: `src/components/layout/header.tsx`

**Props**:
- `onMenuClick: () => void` - Callback when hamburger menu is clicked
- `title?: string` - Optional page title

**Features**:
- Sticky positioning (stays at top when scrolling)
- Hamburger menu button (mobile only)
- Optional page title display
- User menu dropdown on right

### UserMenu

User profile dropdown menu component.

**Location**: `src/components/layout/user-menu.tsx`

**Features**:
- User avatar with initials
- Dropdown menu with:
  - User email and role badge
  - Profile link (placeholder)
  - Settings link (placeholder)
  - Logout button
- Role badge (admin/user)
- Active status indicator
- Handles logout and redirects to login page

**Logout Flow**:
1. Calls `apiClient.logout()`
2. Clears auth store
3. Redirects to `/auth/login`

## Navigation Configuration

**Location**: `src/lib/navigation.ts`

Centralized navigation configuration with icon mappings.

```typescript
export interface NavigationItem {
  name: string;
  href: string;
  icon: LucideIcon;
  adminOnly?: boolean;
}
```

**Adding New Navigation Items**:
1. Add item to `navigation` array in `src/lib/navigation.ts`
2. Import appropriate icon from `lucide-react`
3. Set `adminOnly: true` for admin-only pages

## Layout Patterns

### Page Layouts

Each major section has its own layout file that wraps pages with `AppLayout` and `ProtectedRoute`:

- `/dashboard` → `src/app/dashboard/layout.tsx`
- `/sessions` → `src/app/sessions/layout.tsx`
- `/tasks` → `src/app/tasks/layout.tsx`
- `/mcp-servers` → `src/app/mcp-servers/layout.tsx`
- `/reports` → `src/app/reports/layout.tsx`
- `/admin` → `src/app/admin/layout.tsx`

**Example Layout**:
```tsx
'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';

export default function MyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}
```

### Page Content

Pages should focus on their content and not include authentication or layout logic:

```tsx
'use client';

export default function MyPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Page Title</h1>
        <Button>Action</Button>
      </div>

      <div>
        {/* Page content */}
      </div>
    </div>
  );
}
```

## Responsive Behavior

### Desktop (lg and above)
- Sidebar: Fixed, always visible (260px width)
- Header: Hamburger menu hidden
- Content: Takes remaining space

### Mobile (below lg)
- Sidebar: Hidden by default, opens as overlay
- Header: Hamburger menu visible
- Content: Full width
- Sidebar overlay: Dark background with close on click

## Styling

All components use Tailwind CSS with shadcn/ui components:
- Consistent spacing with `px-6`, `py-4`, etc.
- Uses theme colors (`bg-background`, `text-muted-foreground`, etc.)
- Responsive classes (`lg:`, `md:`, etc.)
- Smooth transitions (`transition-transform`, `duration-300`)

## Dependencies

- `next/navigation` - For routing and pathname detection
- `lucide-react` - For icons
- `@/components/ui/*` - shadcn/ui components
- `@/store/auth-store` - User authentication state
- `@/lib/api-client` - API calls (logout)

## Future Enhancements

- [ ] Breadcrumb navigation
- [ ] Search functionality
- [ ] Notifications dropdown
- [ ] Theme switcher (dark/light mode)
- [ ] Profile settings page
- [ ] User preferences (sidebar collapsed state persistence)

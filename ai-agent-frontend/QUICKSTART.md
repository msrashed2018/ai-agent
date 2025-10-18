# Quick Start Guide - AI Agent Frontend

Get the AI Agent Frontend up and running in 5 minutes!

---

## Prerequisites

✅ **Node.js 18+** installed ([Download here](https://nodejs.org))
✅ **AI Agent API** running at `http://localhost:8000`
✅ Terminal/Command prompt access

---

## 🚀 Installation (2 minutes)

### Step 1: Navigate to the Frontend Directory

```bash
cd /workspace/me/repositories/kubemind/ai-agent-frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

This will install all required packages (~200MB, takes 1-2 minutes).

### Step 3: Verify Environment Configuration

The `.env.local` file is already configured:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If your API is running on a different URL, update this value.

---

## 🎯 Running the Application (30 seconds)

### Start Development Server

```bash
npm run dev
```

You should see:

```
✓ Ready in 2.5s
○ Local:        http://localhost:3000
○ Network:      http://192.168.x.x:3000
```

### Open in Browser

Navigate to **[http://localhost:3000](http://localhost:3000)**

You'll be automatically redirected to the login page.

---

## 🔑 First Login

### Use Your API Credentials

The default admin credentials depend on your API setup. Common defaults:

- **Email**: `admin@example.com`
- **Password**: `admin` (or your configured password)

> **Note**: Credentials are managed by the AI Agent API service. Check your API documentation for exact login details.

### After Login

You'll be redirected to the **Dashboard** where you can:

1. ✅ View session statistics
2. ✅ See recent sessions
3. ✅ Access quick actions
4. ✅ Navigate to all features

---

## 📱 Main Features Overview

### 1. Dashboard (`/dashboard`)
- Overview of your sessions, tasks, and costs
- Recent activity feed
- Quick action buttons

### 2. Sessions (`/sessions`)
- **List**: View all your AI sessions
- **Create**: Start a new session with custom configuration
- **Query**: Chat interface to interact with sessions
- **Detail**: View messages, tool calls, and session stats

### 3. Tasks (`/tasks`)
- **List**: View all automation tasks
- **Create**: Set up scheduled or manual tasks
- **Execute**: Run tasks with custom variables
- **History**: View execution logs and results

### 4. MCP Servers (`/mcp-servers`)
- **List**: Manage MCP server configurations
- **Create**: Add new MCP servers (stdio, SSE, HTTP)
- **Import**: Upload Claude Desktop config
- **Export**: Download your server configurations
- **Templates**: Browse and use pre-configured templates

### 5. Reports (`/reports`)
- **List**: View all generated reports
- **View**: Preview report content
- **Download**: Get reports in HTML, PDF, JSON, or Markdown

### 6. Admin Dashboard (`/admin`) 🔒
*(Admin users only)*
- **System Stats**: Overall platform statistics
- **All Sessions**: View sessions from all users
- **All Users**: Manage user accounts

---

## 🎨 Navigation

### Sidebar Menu (Left)

- **Dashboard** - Overview and stats
- **Sessions** - AI session management
- **Tasks** - Automation and scheduling
- **MCP Servers** - MCP server configuration
- **Reports** - Generated reports
- **Admin** - System administration (admin only)

### User Menu (Top Right)

- **Profile** - User settings (coming soon)
- **Settings** - Application preferences (coming soon)
- **Logout** - Sign out

---

## 🛠️ Development Commands

### Type Checking

```bash
npm run type-check
```

Runs TypeScript compiler to check for type errors.

### Linting

```bash
npm run lint
```

Runs ESLint to check for code quality issues.

### Production Build

```bash
npm run build
```

Creates an optimized production build in `.next/` directory.

### Production Start

```bash
npm run build
npm start
```

Runs the production build locally on port 3000.

---

## 🔧 Configuration

### API URL

To change the API endpoint, update `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

Restart the dev server for changes to take effect.

### Port

To run on a different port:

```bash
PORT=3001 npm run dev
```

Or update `package.json`:

```json
{
  "scripts": {
    "dev": "next dev -p 3001"
  }
}
```

---

## 📊 Common Tasks

### Create a New Session

1. Navigate to **Sessions** → Click **Create Session**
2. Fill in:
   - **Name**: My First Session
   - **Model**: claude-sonnet-4-5-20250929
   - **Allowed Tools**: Select tools
   - **System Prompt**: (optional)
3. Click **Create**
4. Click **Query** to start chatting

### Create and Execute a Task

1. Navigate to **Tasks** → Click **Create Task**
2. Fill in:
   - **Name**: Daily Report
   - **Prompt Template**: Generate a daily report
   - **Variables**: Add any template variables
   - **Schedule**: Set cron expression (optional)
3. Click **Create**
4. Click **Execute** to run manually

### Add an MCP Server

1. Navigate to **MCP Servers** → Click **Create Server**
2. Select server type (stdio, SSE, or HTTP)
3. Fill in configuration:
   - **stdio**: Command and arguments
   - **SSE**: URL and headers
   - **HTTP**: URL and headers
4. Click **Test Connection** (optional)
5. Click **Create**

### Import Claude Desktop Config

1. Navigate to **MCP Servers** → Click **Import Config**
2. Drag & drop your `claude_desktop_config.json` file
3. Preview detected servers
4. Click **Import**

---

## 🐛 Troubleshooting

### Issue: "Failed to fetch" errors

**Solution**: Ensure the AI Agent API is running at `http://localhost:8000`

```bash
# Check if API is running
curl http://localhost:8000/api/v1/health
```

### Issue: Login fails

**Solution**: Check your API credentials and ensure the API is accessible

### Issue: TypeScript errors

**Solution**: Run type check to see details

```bash
npm run type-check
```

### Issue: Build fails

**Solution**: Clean install dependencies

```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue: Page doesn't load

**Solution**: Check browser console for errors (F12 → Console)

### Issue: Changes not reflecting

**Solution**: Hard refresh the browser (Ctrl+Shift+R or Cmd+Shift+R)

---

## 🎯 Next Steps

### Explore Features

1. ✅ **Create your first session** and query it
2. ✅ **Set up a task** with a schedule
3. ✅ **Add MCP servers** for enhanced functionality
4. ✅ **View reports** generated from tasks
5. ✅ **Check admin dashboard** (if you're an admin)

### Customize

- Update color scheme in `tailwind.config.ts`
- Modify navigation in `src/lib/navigation.ts`
- Add custom components in `src/components/`

### Deploy to Production

See [README.md](README.md) for deployment instructions.

---

## 📚 Documentation

- **Full Documentation**: [README.md](README.md)
- **Implementation Plan**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Completion Summary**: [FRONTEND_COMPLETE.md](FRONTEND_COMPLETE.md)
- **Agent Tasks**: [AGENT_TASKS.md](AGENT_TASKS.md)

---

## 💡 Tips

### Keyboard Shortcuts (Coming Soon)
- `Ctrl+K` - Global command palette
- `Ctrl+/` - Focus search
- `Esc` - Close dialogs

### Performance
- Use **React Query DevTools** to inspect cache
- Check **Network tab** for API response times
- Monitor **Console** for warnings

### Best Practices
- **Sessions**: Name your sessions descriptively
- **Tasks**: Use clear variable names in templates
- **MCP Servers**: Test connections before creating
- **Reports**: Tag reports for easy filtering

---

## 🆘 Support

### Resources
- **API Documentation**: `http://localhost:8000/docs`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`
- **Next.js Docs**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs

### Common Questions

**Q: Can I use this with a remote API?**
A: Yes! Update `NEXT_PUBLIC_API_URL` in `.env.local` to point to your remote API.

**Q: Is authentication required?**
A: Yes. All pages (except login) require authentication. Tokens are stored in localStorage.

**Q: Can I customize the UI?**
A: Absolutely! Tailwind CSS and shadcn/ui make it easy to customize colors, spacing, and components.

**Q: Does it work on mobile?**
A: Yes! The UI is fully responsive and works on mobile, tablet, and desktop.

---

## ✅ Success!

You're now ready to use the AI Agent Frontend! 🎉

Start by creating your first session and exploring the features.

---

*Happy automating!* 🚀

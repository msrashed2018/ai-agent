"""HTTP client for AI-Agent-API-Service."""

import httpx
from typing import Any, Dict, Optional
from pathlib import Path

from ai_agent_cli.core.config import config_manager
from ai_agent_cli.core.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)


class APIClient:
    """HTTP client for interacting with AI-Agent-API-Service."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        """Initialize API client."""
        self.base_url = (base_url or config_manager.get_api_url()).rstrip("/")
        self.token = token or config_manager.get_access_token()
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed. Please login again.")
        elif response.status_code == 403:
            raise AuthenticationError("Access forbidden. Insufficient permissions.")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found.")
        elif response.status_code == 422:
            try:
                error_data = response.json()
                raise ValidationError(f"Validation error: {error_data}")
            except Exception:
                raise ValidationError("Validation error.")
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                raise APIError(f"API error: {error_data.get('detail', response.text)}")
            except Exception:
                raise APIError(f"API error: {response.status_code} - {response.text}")

        try:
            return response.json()
        except Exception:
            return response.text if response.text else None

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            return self._handle_response(response)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        if files:
            # For file uploads, remove Content-Type header (httpx will set it)
            headers.pop("Content-Type", None)

        with httpx.Client(timeout=self.timeout) as client:
            if files:
                response = client.post(url, headers=headers, data=data, files=files)
            else:
                response = client.post(url, headers=headers, json=data)
            return self._handle_response(response)

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Make PATCH request."""
        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.patch(url, headers=self._get_headers(), json=data)
            return self._handle_response(response)

    def delete(self, endpoint: str) -> Any:
        """Make DELETE request."""
        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(url, headers=self._get_headers())
            if response.status_code == 204:
                return None
            return self._handle_response(response)

    def download_file(self, endpoint: str, output_path: Path) -> None:
        """Download file from API."""
        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("GET", url, headers=self._get_headers()) as response:
                if response.status_code >= 400:
                    raise APIError(f"Failed to download file: {response.status_code}")

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)

    # Authentication endpoints
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get tokens."""
        return self.post("/api/v1/auth/login", {"email": email, "password": password})

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        return self.post("/api/v1/auth/refresh", {"refresh_token": refresh_token})

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        return self.get("/api/v1/auth/me")

    # Session endpoints
    def create_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session."""
        return self.post("/api/v1/sessions", data)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session by ID."""
        return self.get(f"/api/v1/sessions/{session_id}")

    def list_sessions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List sessions."""
        return self.get("/api/v1/sessions", params)

    def send_message(self, session_id: str, message: str, fork: bool = False) -> Dict[str, Any]:
        """Send message to session."""
        return self.post(f"/api/v1/sessions/{session_id}/query", {"message": message, "fork": fork})

    def list_messages(self, session_id: str, limit: int = 50) -> list:
        """List messages in session."""
        return self.get(f"/api/v1/sessions/{session_id}/messages", {"limit": limit})

    def list_tool_calls(self, session_id: str, limit: int = 50) -> list:
        """List tool calls in session."""
        return self.get(f"/api/v1/sessions/{session_id}/tool-calls", {"limit": limit})

    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pause a session."""
        return self.post(f"/api/v1/sessions/{session_id}/pause", {})

    def resume_session(self, session_id: str, fork: bool = False) -> Dict[str, Any]:
        """Resume a session."""
        return self.post(f"/api/v1/sessions/{session_id}/resume", {"fork": fork})

    def terminate_session(self, session_id: str) -> None:
        """Terminate a session."""
        return self.delete(f"/api/v1/sessions/{session_id}")

    def download_working_directory(self, session_id: str, output_path: Path) -> None:
        """Download session working directory."""
        self.download_file(f"/api/v1/sessions/{session_id}/workdir/download", output_path)

    # Task endpoints
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        return self.post("/api/v1/tasks", data)

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task by ID."""
        return self.get(f"/api/v1/tasks/{task_id}")

    def list_tasks(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List tasks."""
        return self.get("/api/v1/tasks", params)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update task."""
        return self.patch(f"/api/v1/tasks/{task_id}", data)

    def delete_task(self, task_id: str) -> None:
        """Delete task."""
        return self.delete(f"/api/v1/tasks/{task_id}")

    def execute_task(self, task_id: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute task."""
        return self.post(f"/api/v1/tasks/{task_id}/execute", {"variables": variables or {}})

    def list_task_executions(self, task_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List task executions."""
        return self.get(f"/api/v1/tasks/{task_id}/executions", params)

    def get_task_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get task execution."""
        return self.get(f"/api/v1/tasks/executions/{execution_id}")

    # Report endpoints
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get report by ID."""
        return self.get(f"/api/v1/reports/{report_id}")

    def list_reports(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List reports."""
        return self.get("/api/v1/reports", params)

    def download_report(self, report_id: str, format: str, output_path: Path) -> None:
        """Download report."""
        self.download_file(f"/api/v1/reports/{report_id}/download?format={format}", output_path)

    # MCP Server endpoints
    def list_mcp_servers(self) -> Dict[str, Any]:
        """List MCP servers."""
        return self.get("/api/v1/mcp-servers")

    def create_mcp_server(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create MCP server."""
        return self.post("/api/v1/mcp-servers", data)

    def get_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """Get MCP server."""
        return self.get(f"/api/v1/mcp-servers/{server_id}")

    def update_mcp_server(self, server_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update MCP server."""
        return self.patch(f"/api/v1/mcp-servers/{server_id}", data)

    def delete_mcp_server(self, server_id: str) -> None:
        """Delete MCP server."""
        return self.delete(f"/api/v1/mcp-servers/{server_id}")

    def health_check_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """Health check MCP server."""
        return self.post(f"/api/v1/mcp-servers/{server_id}/health-check", {})

    def import_claude_desktop_config(self, file_path: Path, override_existing: bool = False) -> Dict[str, Any]:
        """Import Claude Desktop config."""
        with open(file_path, "rb") as f:
            files = {"file": ("config.json", f, "application/json")}
            return self.post(
                "/api/v1/mcp-servers/import",
                data={"override_existing": str(override_existing).lower()},
                files=files,
            )

    def export_claude_desktop_config(self, include_global: bool = True) -> Dict[str, Any]:
        """Export Claude Desktop config."""
        return self.get("/api/v1/mcp-servers/export", {"include_global": include_global})

    def get_mcp_templates(self) -> Dict[str, Any]:
        """Get MCP server templates."""
        return self.get("/api/v1/mcp-servers/templates")

    # Admin endpoints
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics (admin only)."""
        return self.get("/api/v1/admin/stats")

    def list_all_sessions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all sessions (admin only)."""
        return self.get("/api/v1/admin/sessions", params)

    def list_all_users(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all users (admin only)."""
        return self.get("/api/v1/admin/users", params)


def get_client() -> APIClient:
    """Get configured API client instance."""
    return APIClient()

"""Seed default task templates."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.task_template import TaskTemplateModel


DEFAULT_TEMPLATES = [
    {
        "name": "Kubernetes Health Check",
        "description": "Comprehensive health check for Kubernetes cluster including nodes, pods, deployments, and services",
        "category": "kubernetes",
        "icon": "kubernetes",
        "prompt_template": """Perform a comprehensive health check on the Kubernetes cluster:

1. Check cluster nodes status
2. List all pods and their status
3. Check for any failing deployments or replica sets
4. Review recent events and errors
5. Check resource utilization (CPU, memory)
6. Verify critical services are running

Cluster context: {{cluster_context|default('default')}}
Namespace: {{namespace|default('all')}}

Provide a summary of the cluster health and any issues found.""",
        "template_variables_schema": {
            "type": "object",
            "properties": {
                "cluster_context": {
                    "type": "string",
                    "description": "Kubernetes cluster context name",
                    "default": "default"
                },
                "namespace": {
                    "type": "string",
                    "description": "Namespace to check (or 'all' for all namespaces)",
                    "default": "all"
                }
            }
        },
        "allowed_tools": ["bash", "read", "list_directory"],
        "sdk_options": {
            "model": "claude-sonnet-4",
            "max_turns": 15
        },
        "generate_report": True,
        "report_format": "html",
        "tags": ["kubernetes", "infrastructure", "monitoring", "devops"],
    },
    {
        "name": "Docker Container Monitoring",
        "description": "Monitor Docker containers, check health status, resource usage, and logs",
        "category": "docker",
        "icon": "docker",
        "prompt_template": """Monitor Docker containers and provide a health report:

1. List all running containers
2. Check container health status
3. Review resource usage (CPU, memory, network)
4. Check for containers with restart loops
5. Inspect logs of {{container_name|default('all containers')}} for errors
6. Check disk space usage

Container name filter: {{container_name|default('all')}}
Time range for logs: {{log_time_range|default('last 1 hour')}}

Provide a summary of container health and any issues detected.""",
        "template_variables_schema": {
            "type": "object",
            "properties": {
                "container_name": {
                    "type": "string",
                    "description": "Specific container name to monitor (or 'all')",
                    "default": "all"
                },
                "log_time_range": {
                    "type": "string",
                    "description": "Time range for log inspection",
                    "default": "last 1 hour"
                }
            }
        },
        "allowed_tools": ["bash", "read"],
        "sdk_options": {
            "model": "claude-sonnet-4",
            "max_turns": 12
        },
        "generate_report": True,
        "report_format": "html",
        "tags": ["docker", "containers", "monitoring", "devops"],
    },
    {
        "name": "Git Repository Analysis",
        "description": "Analyze Git repository for code quality, commit history, and potential issues",
        "category": "git",
        "icon": "git",
        "prompt_template": """Analyze the Git repository and provide insights:

1. Repository statistics (commits, contributors, branches)
2. Recent commit activity and patterns
3. Code churn analysis (files changed frequently)
4. Large files or potential repository bloat
5. Branch status (merged, stale, active)
6. Review recent {{commits_to_review|default('10')}} commits for quality

Repository path: {{repo_path|default('.')}}
Branch: {{branch|default('main')}}

Provide a comprehensive analysis with recommendations.""",
        "template_variables_schema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Path to the Git repository",
                    "default": "."
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to analyze",
                    "default": "main"
                },
                "commits_to_review": {
                    "type": "integer",
                    "description": "Number of recent commits to review",
                    "default": 10
                }
            }
        },
        "allowed_tools": ["bash", "read", "grep", "list_directory"],
        "sdk_options": {
            "model": "claude-sonnet-4",
            "max_turns": 20
        },
        "generate_report": True,
        "report_format": "markdown",
        "tags": ["git", "code-quality", "version-control", "development"],
    },
    {
        "name": "Log File Analysis",
        "description": "Analyze log files for errors, warnings, patterns, and anomalies",
        "category": "monitoring",
        "icon": "file-search",
        "prompt_template": """Analyze log files and identify issues:

1. Search for ERROR and WARNING level messages
2. Identify common error patterns
3. Detect anomalies or unusual activity
4. Count frequency of different error types
5. Extract stack traces for critical errors
6. Identify time ranges with high error rates

Log file path: {{log_path}}
Time range: {{time_range|default('last 24 hours')}}
Error threshold: {{error_threshold|default('100')}} errors to highlight

Provide a summary of findings with recommendations.""",
        "template_variables_schema": {
            "type": "object",
            "properties": {
                "log_path": {
                    "type": "string",
                    "description": "Path to the log file or directory",
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range to analyze",
                    "default": "last 24 hours"
                },
                "error_threshold": {
                    "type": "integer",
                    "description": "Minimum error count to highlight",
                    "default": 100
                }
            },
            "required": ["log_path"]
        },
        "allowed_tools": ["bash", "read", "grep"],
        "sdk_options": {
            "model": "claude-sonnet-4",
            "max_turns": 15
        },
        "generate_report": True,
        "report_format": "html",
        "tags": ["logs", "monitoring", "debugging", "troubleshooting"],
    },
    {
        "name": "Database Backup Verification",
        "description": "Verify database backups are recent, complete, and restorable",
        "category": "database",
        "icon": "database",
        "prompt_template": """Verify database backup integrity and status:

1. Check backup files exist and are recent
2. Verify backup file sizes are reasonable (not empty or corrupted)
3. Check backup timestamps and frequency
4. Validate backup naming conventions
5. Test backup accessibility and permissions
6. Review backup retention policy compliance

Backup directory: {{backup_dir}}
Database type: {{db_type|default('postgresql')}}
Expected backup frequency: {{backup_frequency|default('daily')}}
Retention days: {{retention_days|default('30')}}

Provide a backup health report with any issues found.""",
        "template_variables_schema": {
            "type": "object",
            "properties": {
                "backup_dir": {
                    "type": "string",
                    "description": "Directory containing backup files",
                },
                "db_type": {
                    "type": "string",
                    "description": "Database type (postgresql, mysql, mongodb, etc.)",
                    "default": "postgresql"
                },
                "backup_frequency": {
                    "type": "string",
                    "description": "Expected backup frequency",
                    "default": "daily"
                },
                "retention_days": {
                    "type": "integer",
                    "description": "Expected retention period in days",
                    "default": 30
                }
            },
            "required": ["backup_dir"]
        },
        "allowed_tools": ["bash", "read", "list_directory"],
        "sdk_options": {
            "model": "claude-sonnet-4",
            "max_turns": 10
        },
        "generate_report": True,
        "report_format": "html",
        "tags": ["database", "backup", "verification", "reliability"],
    },
]


async def seed_templates():
    """Seed default task templates."""
    print("🌱 Seeding task templates...")

    async with AsyncSessionLocal() as db:
        # Check which templates already exist
        for template_data in DEFAULT_TEMPLATES:
            result = await db.execute(
                select(TaskTemplateModel).where(
                    TaskTemplateModel.name == template_data["name"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  ⏭️  Template '{template_data['name']}' already exists, skipping")
                continue

            # Create new template
            template = TaskTemplateModel(
                id=uuid4(),
                name=template_data["name"],
                description=template_data["description"],
                category=template_data["category"],
                icon=template_data["icon"],
                prompt_template=template_data["prompt_template"],
                template_variables_schema=template_data.get("template_variables_schema"),
                allowed_tools=template_data["allowed_tools"],
                disallowed_tools=[],
                sdk_options=template_data["sdk_options"],
                generate_report=template_data.get("generate_report", False),
                report_format=template_data.get("report_format"),
                tags=template_data.get("tags", []),
                is_public=True,
                is_active=True,
                usage_count=0,
            )

            db.add(template)
            print(f"  ✅ Created template: {template_data['name']}")

        await db.commit()
        print("\n✨ Task templates seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_templates())

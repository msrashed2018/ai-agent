"""Seed tasks with sample configurations."""

import logging
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserModel
from app.models.tool_group import ToolGroupModel
from app.models.task import TaskModel

logger = logging.getLogger(__name__)


# Default tasks for development and testing
DEFAULT_TASKS = [
    {
        "name": "Daily Infrastructure Health Check",
        "description": "Automated daily health check for infrastructure components including Kubernetes and Docker",
        "prompt_template": """Perform a comprehensive infrastructure health check:

1. Check Kubernetes cluster status
   - Node status and health
   - Pod status across all namespaces
   - Deployment replicas matching desired state

2. Check Docker containers
   - List all running containers
   - Check for containers with restart loops
   - Monitor resource usage

3. Generate summary report with:
   - Overall health status
   - Any critical issues found
   - Recommended actions

Time: {{check_time|default('daily 2 AM UTC')}}
Cluster context: {{cluster_context|default('production')}}""",
        "default_variables": {
            "cluster_context": "production",
            "check_time": "daily 2 AM UTC"
        },
        "allowed_tools": ["bash", "read", "grep"],
        "sdk_options": {"model": "claude-sonnet-4", "max_turns": 15},
        "generate_report": True,
        "report_format": "html",
        "tags": ["infrastructure", "kubernetes", "docker", "monitoring", "automated"],
        "is_scheduled": True,
        "schedule_cron": "0 2 * * *",
        "schedule_enabled": False,
        "is_public": True
    },
    {
        "name": "Weekly Git Repository Analysis",
        "description": "Weekly analysis of Git repositories for code quality and commit patterns",
        "prompt_template": """Analyze Git repositories for development insights:

1. Repository Statistics
   - Total commits this week
   - Number of contributors
   - Most active developers

2. Code Quality Analysis
   - Files with most changes
   - Potential code churn areas
   - Large commits (potential refactoring)

3. Branch Health
   - List merged branches
   - Identify stale branches
   - Active development branches

Repository path: {{repo_path|default('.')}}
Branch to analyze: {{main_branch|default('main')}}

Provide actionable insights for the team.""",
        "default_variables": {
            "repo_path": ".",
            "main_branch": "main"
        },
        "allowed_tools": ["bash", "read", "grep", "glob"],
        "sdk_options": {"model": "claude-sonnet-4", "max_turns": 20},
        "generate_report": True,
        "report_format": "markdown",
        "tags": ["git", "code-quality", "development", "weekly", "automated"],
        "is_scheduled": True,
        "schedule_cron": "0 9 * * 1",
        "schedule_enabled": False,
        "is_public": True
    },
    {
        "name": "Log Analysis for Errors",
        "description": "Analyze application logs for errors, warnings, and anomalies",
        "prompt_template": """Analyze application logs and identify issues:

1. Error Summary
   - Count errors by type
   - Top 10 error messages
   - Error frequency over time

2. Warning Analysis
   - Critical warnings
   - Warning patterns
   - Affected components

3. Anomaly Detection
   - Unusual error spikes
   - New error types
   - Performance anomalies

Log path: {{log_path|default('/var/log/app/')}}
Hours to analyze: {{hours|default('24')}}
Minimum error count to report: {{min_errors|default('10')}}

Generate diagnostic report with recommendations.""",
        "default_variables": {
            "log_path": "/var/log/app/",
            "hours": 24,
            "min_errors": 10
        },
        "allowed_tools": ["bash", "read", "grep"],
        "sdk_options": {"model": "claude-sonnet-4", "max_turns": 15},
        "generate_report": True,
        "report_format": "html",
        "tags": ["logs", "monitoring", "debugging", "troubleshooting"],
        "is_scheduled": True,
        "schedule_cron": "0 */4 * * *",
        "schedule_enabled": False,
        "is_public": True
    },
    {
        "name": "Database Backup Verification",
        "description": "Verify database backups are recent, complete, and restorable",
        "prompt_template": """Verify database backup status and integrity:

1. Backup Files
   - Check if backups exist
   - Verify file sizes (not corrupted)
   - Check backup timestamps
   - Verify recent backups (within {{max_age_hours|default('24')}} hours)

2. Backup Format Validation
   - Verify naming conventions
   - Check file integrity
   - Validate backup format ({{backup_format|default('sql')}})

3. Backup Storage
   - Available storage space
   - Backup retention compliance
   - Archive status

Backup directory: {{backup_dir|default('/var/backups/postgresql')}}
Database type: {{db_type|default('postgresql')}}
Expected frequency: {{frequency|default('daily')}}
Retention days: {{retention_days|default('30')}}

Generate backup health report.""",
        "default_variables": {
            "backup_dir": "/var/backups/postgresql",
            "db_type": "postgresql",
            "frequency": "daily",
            "retention_days": 30,
            "max_age_hours": 24
        },
        "allowed_tools": ["bash", "read", "glob"],
        "sdk_options": {"model": "claude-sonnet-4", "max_turns": 10},
        "generate_report": True,
        "report_format": "html",
        "tags": ["database", "backup", "verification", "reliability"],
        "is_scheduled": True,
        "schedule_cron": "0 3 * * *",
        "schedule_enabled": False,
        "is_public": True
    },
    {
        "name": "Docker Container Resource Monitoring",
        "description": "Monitor Docker container resource usage and health",
        "prompt_template": """Monitor Docker container performance:

1. Resource Usage
   - CPU usage per container
   - Memory usage and limits
   - Network I/O statistics
   - Disk I/O statistics

2. Health Checks
   - Container health status
   - Restart count and frequency
   - Exit code analysis
   - Uptime analysis

3. Container Status
   - Running vs stopped containers
   - Containers with resource constraints
   - Memory pressure situations
   - CPU throttling

Container filter: {{container_filter|default('all')}}
Time range: {{time_range|default('last 24 hours')}}
Alert threshold - CPU: {{cpu_threshold|default('80')}}%
Alert threshold - Memory: {{mem_threshold|default('85')}}%

Generate resource utilization report with alerts.""",
        "default_variables": {
            "container_filter": "all",
            "time_range": "last 24 hours",
            "cpu_threshold": 80,
            "mem_threshold": 85
        },
        "allowed_tools": ["bash", "read"],
        "sdk_options": {"model": "claude-sonnet-4", "max_turns": 12},
        "generate_report": True,
        "report_format": "html",
        "tags": ["docker", "containers", "monitoring", "performance", "resources"],
        "is_scheduled": True,
        "schedule_cron": "0 */6 * * *",
        "schedule_enabled": False,
        "is_public": True
    }
]


async def seed_tasks(db: AsyncSession) -> None:
    """Seed default tasks.

    Creates sample tasks that can be executed immediately or scheduled for
    regular execution. Tasks are assigned to the admin user and use seeded
    tool groups where applicable.

    Args:
        db: AsyncSession for database operations
    """
    logger.info("Seeding tasks...")

    # Get admin user to assign tasks to
    result = await db.execute(
        select(UserModel).where(UserModel.username == "admin")
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        logger.warning("  Admin user not found, skipping tasks seeding")
        return

    # Get development tools group (created by tool_groups seeding)
    result = await db.execute(
        select(ToolGroupModel).where(
            ToolGroupModel.name == "Development Tools",
            ToolGroupModel.user_id == admin_user.id
        )
    )
    dev_tool_group = result.scalar_one_or_none()

    # Get devops tools group
    result = await db.execute(
        select(ToolGroupModel).where(
            ToolGroupModel.name == "DevOps Tools",
            ToolGroupModel.user_id == admin_user.id
        )
    )
    devops_tool_group = result.scalar_one_or_none()

    # Check which tasks already exist
    for task_data in DEFAULT_TASKS:
        result = await db.execute(
            select(TaskModel).where(
                TaskModel.name == task_data["name"],
                TaskModel.user_id == admin_user.id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"  Task '{task_data['name']}' already exists, skipping")
            continue

        # Assign appropriate tool group based on task type
        tool_group_id = None
        if "Infrastructure" in task_data["name"] or "Docker" in task_data["name"]:
            tool_group_id = devops_tool_group.id if devops_tool_group else None
        elif "Git" in task_data["name"] or "Code" in task_data["name"]:
            tool_group_id = dev_tool_group.id if dev_tool_group else None
        else:
            tool_group_id = dev_tool_group.id if dev_tool_group else None

        # Create new task
        task = TaskModel(
            id=uuid4(),
            user_id=admin_user.id,
            tool_group_id=tool_group_id,
            name=task_data["name"],
            description=task_data["description"],
            prompt_template=task_data["prompt_template"],
            default_variables=task_data.get("default_variables"),
            allowed_tools=task_data["allowed_tools"],
            disallowed_tools=[],
            sdk_options=task_data.get("sdk_options", {}),
            is_scheduled=task_data.get("is_scheduled", False),
            schedule_cron=task_data.get("schedule_cron"),
            schedule_enabled=task_data.get("schedule_enabled", False),
            generate_report=task_data.get("generate_report", False),
            report_format=task_data.get("report_format"),
            tags=task_data.get("tags", []),
            is_public=task_data.get("is_public", False),
            is_active=True,
        )

        db.add(task)
        logger.info(f"  ✅ Created task: {task_data['name']}")

    await db.commit()
    logger.info("Tasks seeded successfully!")

#!/usr/bin/env python3
"""
Production-Ready Example - Claude Agent SDK

This script demonstrates:
- Production-quality error handling and retry logic
- Comprehensive logging and monitoring with JSON format
- Security best practices with type-safe configuration
- Graceful error recovery
- Performance tracking and metrics export
"""

import asyncio
import logging
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    ClaudeSDKError,
    CLIConnectionError,
)


# Configure production-grade logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

@dataclass
class ProductionConfig:
    """Production configuration with validation and type safety."""

    # Core settings
    model: str = "claude-sonnet-4-5"
    permission_mode: str = "default"
    max_turns: int = 10

    # Security settings
    allowed_tools: List[str] = field(default_factory=lambda: ["python", "read_file", "write_file", "bash"])
    blocked_commands: List[str] = field(default_factory=lambda: ["rm -rf", "sudo rm", "format"])

    # Performance settings
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout_seconds: int = 120

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues.

        Returns:
            List of validation error messages
        """
        issues: List[str] = []

        if self.max_turns < 1:
            issues.append("max_turns must be >= 1")

        if self.max_retries < 0:
            issues.append("max_retries must be >= 0")

        if self.retry_delay < 0:
            issues.append("retry_delay must be >= 0")

        if not self.allowed_tools:
            issues.append("allowed_tools cannot be empty")

        return issues


# ============================================================================
# METRICS COLLECTION
# ============================================================================

@dataclass
class SessionMetrics:
    """Track session performance and usage metrics."""

    session_id: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_messages: int = 0
    total_tool_uses: int = 0
    total_errors: int = 0
    total_retries: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: int = 0

    def complete(self) -> None:
        """Mark session as completed."""
        self.end_time = time.time()

    def duration_seconds(self) -> float:
        """Calculate total session duration in seconds."""
        end: float = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def log_summary(self) -> None:
        """Log session metrics summary in JSON format."""
        logger.info("\nSession Metrics Summary:")
        logger.info(json.dumps({
            "session_id": self.session_id,
            "duration_seconds": round(self.duration_seconds(), 2),
            "total_messages": self.total_messages,
            "total_tool_uses": self.total_tool_uses,
            "total_errors": self.total_errors,
            "total_retries": self.total_retries,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "api_duration_ms": self.total_duration_ms
        }, indent=2))


# ============================================================================
# PRODUCTION CLIENT
# ============================================================================

class ProductionClaudeClient:
    """Production-ready Claude client with error handling and retry logic."""

    def __init__(self, config: ProductionConfig, working_dir: Path):
        self.config: ProductionConfig = config
        self.working_dir: Path = working_dir
        self.metrics: Optional[SessionMetrics] = None

    async def execute_with_retry(self, prompt: str) -> None:
        """Execute query with automatic retry logic.

        Args:
            prompt: The prompt to send to Claude

        Raises:
            ClaudeSDKError: If all retries are exhausted
        """
        session_id: str = str(uuid.uuid4())
        self.metrics = SessionMetrics(session_id=session_id)

        logger.info(f"\nStarting production session: {session_id}")
        logger.info("Configuration:")
        logger.info(json.dumps({
            "model": self.config.model,
            "max_turns": self.config.max_turns,
            "allowed_tools": self.config.allowed_tools,
            "max_retries": self.config.max_retries,
            "retry_delay": self.config.retry_delay
        }, indent=2))

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(f"Attempt #{attempt + 1}/{self.config.max_retries + 1}")

                await self._execute_session(prompt)

                # Success - no retry needed
                break

            except CLIConnectionError as e:
                self.metrics.total_errors += 1
                logger.error(f"Connection error on attempt #{attempt + 1}: {type(e).__name__} - {str(e)}")

                if attempt < self.config.max_retries:
                    self.metrics.total_retries += 1
                    logger.info(f"Retrying in {self.config.retry_delay}s...")
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    logger.error(f"All {self.config.max_retries + 1} attempts failed")
                    raise

            except ClaudeSDKError as e:
                self.metrics.total_errors += 1
                logger.error(f"SDK error: {type(e).__name__} - {str(e)}")
                raise

            except Exception as e:
                self.metrics.total_errors += 1
                logger.error(f"Unexpected error: {type(e).__name__} - {str(e)}", exc_info=True)
                raise

        # Log final metrics
        self.metrics.complete()
        self.metrics.log_summary()

    async def _execute_session(self, prompt: str) -> None:
        """Execute a single session.

        Args:
            prompt: The prompt to send to Claude
        """
        # Create options
        options: ClaudeAgentOptions = ClaudeAgentOptions(
            allowed_tools=self.config.allowed_tools,
            permission_mode=self.config.permission_mode,
            max_turns=self.config.max_turns,
            model=self.config.model,
            cwd=str(self.working_dir)
        )

        logger.info(f"Sending prompt ({len(prompt)} chars): {prompt[:100]}...")

        async with ClaudeSDKClient(options=options) as client:
            logger.info(f"ClaudeSDKClient connected: type={type(client).__name__}")

            await client.query(prompt)

            # Process messages
            async for message in client.receive_response():
                self.metrics.total_messages += 1

                if isinstance(message, AssistantMessage):
                    logger.info(f"\nMessage #{self.metrics.total_messages}: AssistantMessage")
                    logger.info(json.dumps({
                        "model": message.model,
                        "blocks": len(message.content)
                    }, indent=2))

                    for i, block in enumerate(message.content):
                        if isinstance(block, TextBlock):
                            text: str = block.text
                            logger.info(f"\n  Block #{i+1}: TextBlock")
                            logger.info(json.dumps({
                                "length": len(text)
                            }, indent=4))

                        elif isinstance(block, ToolUseBlock):
                            self.metrics.total_tool_uses += 1
                            tool_name: str = block.name
                            tool_input: dict = block.input
                            tool_id: str = block.id

                            logger.info(f"\n  Block #{i+1}: ToolUseBlock")
                            logger.info(json.dumps({
                                "id": tool_id,
                                "name": tool_name,
                                "input": tool_input
                            }, indent=4, default=str))

                        elif isinstance(block, ToolResultBlock):
                            result_content: str = block.content
                            is_error: bool = block.is_error
                            tool_use_id: str = block.tool_use_id

                            logger.info(f"\n  Block #{i+1}: ToolResultBlock")
                            logger.info(json.dumps({
                                "tool_use_id": tool_use_id,
                                "is_error": is_error,
                                "content_length": len(result_content) if isinstance(result_content, str) else 0
                            }, indent=4))

                            if is_error:
                                self.metrics.total_errors += 1

                elif isinstance(message, ResultMessage):
                    duration_ms: int = message.duration_ms
                    cost_usd: Optional[float] = message.total_cost_usd
                    num_turns: int = message.num_turns
                    session_id: str = message.session_id

                    # Update metrics
                    self.metrics.total_duration_ms = duration_ms
                    if cost_usd is not None:
                        self.metrics.total_cost_usd = cost_usd

                    logger.info(f"\nMessage #{self.metrics.total_messages}: ResultMessage")
                    logger.info(json.dumps({
                        "session_id": session_id,
                        "duration_ms": duration_ms,
                        "turns": num_turns,
                        "cost_usd": cost_usd
                    }, indent=2, default=str))
                    break


async def main() -> None:
    """Main function demonstrating production-ready patterns."""

    logger.info("\n" + "=" * 60)
    logger.info("Production-Ready Example")
    logger.info("=" * 60 + "\n")

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Load and validate configuration
    config: ProductionConfig = ProductionConfig()

    logger.info("Configuration Loaded:")
    logger.info(json.dumps({
        "type": type(config).__name__,
        "model": config.model,
        "permission_mode": config.permission_mode,
        "max_turns": config.max_turns,
        "allowed_tools": config.allowed_tools,
        "max_retries": config.max_retries,
        "retry_delay": config.retry_delay,
        "timeout_seconds": config.timeout_seconds
    }, indent=2))

    validation_issues: List[str] = config.validate()
    if validation_issues:
        logger.error("Configuration validation failed:")
        logger.error(json.dumps({"issues": validation_issues}, indent=2))
        return

    logger.info("\n✓ Configuration validation passed")

    # Create production client
    client: ProductionClaudeClient = ProductionClaudeClient(config, working_dir)

    logger.info("\nProductionClaudeClient Created:")
    logger.info(json.dumps({
        "config_model": config.model,
        "working_dir": str(working_dir)
    }, indent=2))

    prompt: str = """
    Create a simple Python script that demonstrates error handling.
    The script should:
    1. Define a function that divides two numbers
    2. Handle division by zero gracefully
    3. Include try/except blocks
    4. Save it to error_handling.py
    5. Run the script to demonstrate it works
    """

    logger.info("\nExecuting production query with retry logic...\n")

    try:
        await client.execute_with_retry(prompt)

        logger.info("\n✓ Production query completed successfully")

        # Export metrics to JSON file
        if client.metrics:
            metrics_file = working_dir / "production_metrics.json"
            metrics_data = {
                "session_id": client.metrics.session_id,
                "start_time": client.metrics.start_time,
                "end_time": client.metrics.end_time,
                "duration_seconds": round(client.metrics.duration_seconds(), 2),
                "total_messages": client.metrics.total_messages,
                "total_tool_uses": client.metrics.total_tool_uses,
                "total_errors": client.metrics.total_errors,
                "total_retries": client.metrics.total_retries,
                "total_cost_usd": round(client.metrics.total_cost_usd, 4),
                "total_duration_ms": client.metrics.total_duration_ms
            }

            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)

            logger.info(f"\nMetrics exported to: {metrics_file}")

    except Exception as e:
        logger.error(f"\n✗ Production query failed: {type(e).__name__} - {str(e)}")

        # Still export partial metrics on error
        if client.metrics:
            metrics_file = working_dir / "production_metrics_error.json"
            metrics_data = {
                "session_id": client.metrics.session_id,
                "start_time": client.metrics.start_time,
                "end_time": client.metrics.end_time,
                "duration_seconds": round(client.metrics.duration_seconds(), 2),
                "total_messages": client.metrics.total_messages,
                "total_tool_uses": client.metrics.total_tool_uses,
                "total_errors": client.metrics.total_errors,
                "total_retries": client.metrics.total_retries,
                "error": str(e),
                "error_type": type(e).__name__
            }

            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)

            logger.info(f"Partial metrics exported to: {metrics_file}")

    logger.info("\n" + "=" * 60)
    logger.info("Completed")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

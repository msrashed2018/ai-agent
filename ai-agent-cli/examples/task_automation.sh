#!/bin/bash
# Example: Task automation workflow

set -e

echo "=== AI Agent CLI Task Automation Example ==="

# 1. Create a task
echo -e "\n1. Creating task..."
TASK_OUTPUT=$(ai-agent tasks create \
  --name "Health Check Task" \
  --description "Automated system health check" \
  --prompt-template "Check the health status of {{service_name}} and report any issues" \
  --allowed-tools "Bash" --allowed-tools "Read" \
  --generate-report \
  --report-format html \
  --tags monitoring --tags automation \
  --format json)

TASK_ID=$(echo $TASK_OUTPUT | jq -r '.id')
echo "Task created: $TASK_ID"

# 2. Execute task with variables
echo -e "\n2. Executing task..."
EXECUTION_OUTPUT=$(ai-agent tasks execute $TASK_ID \
  --variables '{"service_name": "nginx"}' \
  --format json)

EXECUTION_ID=$(echo $EXECUTION_OUTPUT | jq -r '.id')
echo "Execution started: $EXECUTION_ID"

# 3. Wait a bit for execution to complete
echo -e "\n3. Waiting for execution to complete..."
sleep 5

# 4. Check execution status
echo -e "\n4. Checking execution status..."
ai-agent tasks execution-status $EXECUTION_ID --format table

# 5. List all executions for this task
echo -e "\n5. Listing all executions..."
ai-agent tasks executions $TASK_ID --format table

# 6. If report was generated, list reports
echo -e "\n6. Checking for generated reports..."
EXECUTION_DATA=$(ai-agent tasks execution-status $EXECUTION_ID --format json)
REPORT_ID=$(echo $EXECUTION_DATA | jq -r '.report_id // empty')

if [ ! -z "$REPORT_ID" ]; then
  echo "Report generated: $REPORT_ID"
  ai-agent reports download $REPORT_ID --format html --output /tmp/health-check-report.html
  echo "Report downloaded to: /tmp/health-check-report.html"
fi

# 7. Update task (disable it)
echo -e "\n7. Disabling task..."
ai-agent tasks update $TASK_ID --schedule-enabled false

# 8. List all tasks
echo -e "\n8. Listing all tasks..."
ai-agent tasks list --format table

echo -e "\n=== Task automation workflow complete! ==="
echo "Note: To delete the task, run: ai-agent tasks delete $TASK_ID --yes"

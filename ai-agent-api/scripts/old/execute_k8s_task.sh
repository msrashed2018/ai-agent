#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NGQ5ZjVhMi0xMjU3LTQzYWMtOWRlMi02ZDg2NDIxNDU1YTYiLCJleHAiOjE3NjM0MjY0NzksInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiI4ZDQ3Njk0Mi04YmNlLTQzYzAtODY5Mi03MWQ4ZjZkNDhjOTgifQ.MbvYvQqUhegq5fH_fiID2vr9mjUwvPwPhiqPiGz1PxI"
TASK_ID="e65a456f-7841-4397-be65-e2c694ee2a80"

echo "Executing task: $TASK_ID"
echo ""

curl -X POST "http://localhost:8000/api/v1/tasks/${TASK_ID}/execute" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"variables": {}}' | jq '.'

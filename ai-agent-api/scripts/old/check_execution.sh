#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NGQ5ZjVhMi0xMjU3LTQzYWMtOWRlMi02ZDg2NDIxNDU1YTYiLCJleHAiOjE3NjM0MjY0NzksInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiI4ZDQ3Njk0Mi04YmNlLTQzYzAtODY5Mi03MWQ4ZjZkNDhjOTgifQ.MbvYvQqUhegq5fH_fiID2vr9mjUwvPwPhiqPiGz1PxI"
EXECUTION_ID="55f10fb9-3ecd-4ada-ab97-5f7174579cb7"

echo "Checking execution status: $EXECUTION_ID"
echo ""

curl -X GET "http://localhost:8000/api/v1/tasks/executions/${EXECUTION_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'

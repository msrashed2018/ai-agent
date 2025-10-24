#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NGQ5ZjVhMi0xMjU3LTQzYWMtOWRlMi02ZDg2NDIxNDU1YTYiLCJleHAiOjE3NjM0MjY0NzksInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiI4ZDQ3Njk0Mi04YmNlLTQzYzAtODY5Mi03MWQ4ZjZkNDhjOTgifQ.MbvYvQqUhegq5fH_fiID2vr9mjUwvPwPhiqPiGz1PxI"

curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "K8s Cluster Health Check",
    "description": "Comprehensive Kubernetes cluster health check using kubectl - read-only operations",
    "prompt_template": "Please perform a comprehensive health check of the Kubernetes cluster using the kubeconfig file at ~/.kube/config.\n\nYour task:\n1. Check the status of ALL workloads (deployments, statefulsets, daemonsets, jobs, cronjobs)\n2. List and analyze recent events across all namespaces\n3. Check PersistentVolumeClaims (PVCs) status\n4. Check PersistentVolumes (PVs) status\n5. Check node status and resource usage\n6. Identify any pods in non-Running state\n7. Check for any warning or error events\n\nIMPORTANT CONSTRAINTS:\n- Use ONLY read-only kubectl commands (get, describe, logs)\n- Do NOT make any changes to the cluster\n- Do NOT apply, delete, edit, or patch any resources\n\nOutput Requirements:\n- Create a comprehensive markdown report in the working directory named \"k8s-cluster-health-report.md\"\n- Include summary of findings at the top\n- Organize findings by category (workloads, storage, nodes, events)\n- Highlight any issues or warnings found\n- Include timestamps and cluster context information",
    "allowed_tools": ["bash", "write", "read"],
    "sdk_options": {},
    "is_scheduled": false,
    "generate_report": true,
    "report_format": "html",
    "tags": ["kubernetes", "monitoring", "health-check"]
  }' | jq '.'

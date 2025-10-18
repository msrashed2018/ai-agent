"""
SDK MCP Tools - In-process Python tools using @tool decorator.

These are custom tools we define that run in our Python process.
The SDK registers them as MCP tools that Claude can use.
"""

from typing import Any, Dict

# Mock @tool decorator and create_sdk_mcp_server due to SDK issues
try:
    from claude_agent_sdk import tool
    # Note: create_sdk_mcp_server has a bug in v0.1.4 - using our mock instead
except ImportError:
    def tool(name: str, description: str, input_schema: Dict):
        """Mock tool decorator for development."""
        def decorator(func):
            func._tool_name = name
            func._tool_description = description
            func._tool_schema = input_schema
            return func
        return decorator

def create_sdk_mcp_server(name: str, version: str = "1.0.0", tools: list = None):
    """Mock create_sdk_mcp_server - SDK v0.1.4 has a bug in this function."""
    return {
        "type": "sdk",
        "name": name,
        "version": version,
        "tools": tools or []
    }


# ============================================================================
# Kubernetes Tools (Read-Only)
# ============================================================================

@tool(
    name="list_pods",
    description="List all pods in a Kubernetes namespace with their status",
    input_schema={
        "namespace": str,
        "label_selector": str  # Optional: e.g., "app=nginx"
    }
)
async def list_pods(args: Dict[str, Any]) -> Dict[str, Any]:
    """List pods in a namespace."""
    try:
        from kubernetes import client, config
        
        namespace = args.get("namespace", "default")
        label_selector = args.get("label_selector", "")
        
        # Load kubeconfig
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector
        )
        
        # Format pod list
        pod_list = []
        for pod in pods.items:
            pod_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ready": sum(1 for c in pod.status.container_statuses or [] if c.ready),
                "total_containers": len(pod.spec.containers),
                "restarts": sum(c.restart_count for c in pod.status.container_statuses or []),
                "age": str(pod.metadata.creation_timestamp),
                "node": pod.spec.node_name,
                "ip": pod.status.pod_ip
            }
            pod_list.append(pod_info)
        
        # Format as markdown table
        if pod_list:
            table = "| Name | Status | Ready | Restarts | Age | Node |\n"
            table += "|------|--------|-------|----------|-----|------|\n"
            for p in pod_list:
                table += f"| {p['name']} | {p['status']} | {p['ready']}/{p['total_containers']} | {p['restarts']} | {p['age']} | {p['node']} |\n"
            output = table
        else:
            output = f"No pods found in namespace '{namespace}'"
        
        return {
            "content": [{
                "type": "text",
                "text": output
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error listing pods: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="get_pod_logs",
    description="Get logs from a Kubernetes pod",
    input_schema={
        "pod_name": str,
        "namespace": str,
        "container": str,  # Optional
        "tail_lines": int  # Optional: number of lines from end
    }
)
async def get_pod_logs(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get pod logs."""
    try:
        from kubernetes import client, config
        
        pod_name = args["pod_name"]
        namespace = args.get("namespace", "default")
        container = args.get("container")
        tail_lines = args.get("tail_lines", 100)
        
        # Load kubeconfig
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines
        )
        
        return {
            "content": [{
                "type": "text",
                "text": f"Logs for pod '{pod_name}':\n\n```\n{logs}\n```"
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error getting pod logs: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="describe_pod",
    description="Get detailed information about a Kubernetes pod",
    input_schema={
        "pod_name": str,
        "namespace": str
    }
)
async def describe_pod(args: Dict[str, Any]) -> Dict[str, Any]:
    """Describe a pod in detail."""
    try:
        from kubernetes import client, config
        
        pod_name = args["pod_name"]
        namespace = args.get("namespace", "default")
        
        # Load kubeconfig
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        # Build detailed description
        description = f"# Pod: {pod_name}\n\n"
        description += f"**Namespace:** {pod.metadata.namespace}\n"
        description += f"**Status:** {pod.status.phase}\n"
        description += f"**Node:** {pod.spec.node_name}\n"
        description += f"**IP:** {pod.status.pod_ip}\n"
        description += f"**Labels:** {pod.metadata.labels}\n\n"
        
        description += "## Containers\n\n"
        for container in pod.spec.containers:
            description += f"### {container.name}\n"
            description += f"- **Image:** {container.image}\n"
            description += f"- **Ports:** {[p.container_port for p in container.ports or []]}\n"
        
        if pod.status.container_statuses:
            description += "\n## Container Status\n\n"
            for cs in pod.status.container_statuses:
                description += f"### {cs.name}\n"
                description += f"- **Ready:** {cs.ready}\n"
                description += f"- **Restart Count:** {cs.restart_count}\n"
                description += f"- **State:** {cs.state}\n"
        
        return {
            "content": [{
                "type": "text",
                "text": description
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error describing pod: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="list_namespaces",
    description="List all Kubernetes namespaces",
    input_schema={}
)
async def list_namespaces(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all namespaces."""
    try:
        from kubernetes import client, config
        
        # Load kubeconfig
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        
        # Format as list
        ns_list = [ns.metadata.name for ns in namespaces.items]
        output = "**Kubernetes Namespaces:**\n\n" + "\n".join(f"- {ns}" for ns in ns_list)
        
        return {
            "content": [{
                "type": "text",
                "text": output
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error listing namespaces: {str(e)}"
            }],
            "isError": True
        }


# ============================================================================
# Database Tools (Read-Only)
# ============================================================================

@tool(
    name="query_database",
    description="Execute a SELECT query on the database (read-only)",
    input_schema={
        "query": str,
        "limit": int  # Optional: max rows to return (default 100)
    }
)
async def query_database(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute read-only database query."""
    try:
        from sqlalchemy import text
        from app.database.session import get_db
        
        query = args["query"].strip()
        limit = args.get("limit", 100)
        
        # Safety checks - block dangerous operations
        dangerous_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", 
            "CREATE", "TRUNCATE", "GRANT", "REVOKE"
        ]
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error: Query contains dangerous keyword '{keyword}'. Only SELECT queries are allowed."
                    }],
                    "isError": True
                }
        
        # Ensure it's a SELECT query
        if not query_upper.startswith("SELECT"):
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: Only SELECT queries are allowed."
                }],
                "isError": True
            }
        
        # Add LIMIT if not present
        if "LIMIT" not in query_upper:
            query += f" LIMIT {min(limit, 1000)}"
        
        # Execute query
        async for db in get_db():
            result = await db.execute(text(query))
            rows = result.fetchall()
            
            if not rows:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Query returned no results."
                    }]
                }
            
            # Format as markdown table
            columns = result.keys()
            table = "| " + " | ".join(columns) + " |\n"
            table += "|" + "|".join(["---" for _ in columns]) + "|\n"
            
            for row in rows:
                table += "| " + " | ".join(str(v) for v in row) + " |\n"
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Query results ({len(rows)} rows):\n\n{table}"
                }]
            }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error executing query: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="describe_table",
    description="Get the schema of a database table",
    input_schema={
        "table_name": str
    }
)
async def describe_table(args: Dict[str, Any]) -> Dict[str, Any]:
    """Describe a database table schema."""
    try:
        from sqlalchemy import text
        from app.database.session import get_db
        
        table_name = args["table_name"]
        
        # Query information_schema
        query = text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """)
        
        async for db in get_db():
            result = await db.execute(query, {"table_name": table_name})
            columns = result.fetchall()
            
            if not columns:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Table '{table_name}' not found."
                    }],
                    "isError": True
                }
            
            # Format as markdown table
            output = f"# Table: {table_name}\n\n"
            output += "| Column | Type | Nullable | Default |\n"
            output += "|--------|------|----------|----------|\n"
            
            for col in columns:
                output += f"| {col[0]} | {col[1]} | {col[2]} | {col[3] or 'N/A'} |\n"
            
            return {
                "content": [{
                    "type": "text",
                    "text": output
                }]
            }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error describing table: {str(e)}"
            }],
            "isError": True
        }


# ============================================================================
# System Monitoring Tools
# ============================================================================

@tool(
    name="get_system_metrics",
    description="Get current system resource usage (CPU, memory, disk)",
    input_schema={}
)
async def get_system_metrics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get system metrics."""
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
        output = "# System Metrics\n\n"
        output += f"**CPU Usage:** {cpu_percent}% ({cpu_count} cores)\n"
        output += f"**Memory:** {memory_used_gb:.2f}GB / {memory_total_gb:.2f}GB ({memory.percent}%)\n"
        output += f"**Disk:** {disk_used_gb:.2f}GB / {disk_total_gb:.2f}GB ({disk.percent}%)\n"
        
        return {
            "content": [{
                "type": "text",
                "text": output
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error getting system metrics: {str(e)}"
            }],
            "isError": True
        }


# ============================================================================
# Register SDK MCP Servers
# ============================================================================

# Create SDK MCP servers with our tools
kubernetes_server = create_sdk_mcp_server(
    name="kubernetes_readonly",
    version="1.0.0",
    tools=[list_pods, get_pod_logs, describe_pod, list_namespaces]
)

database_server = create_sdk_mcp_server(
    name="database",
    version="1.0.0",
    tools=[query_database, describe_table]
)

monitoring_server = create_sdk_mcp_server(
    name="monitoring",
    version="1.0.0",
    tools=[get_system_metrics]
)

# Export all SDK MCP servers
SDK_MCP_SERVERS = {
    "kubernetes_readonly": kubernetes_server,
    "database": database_server,
    "monitoring": monitoring_server
}

__all__ = ["SDK_MCP_SERVERS"]

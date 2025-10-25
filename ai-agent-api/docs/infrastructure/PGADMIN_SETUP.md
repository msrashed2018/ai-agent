# pgAdmin Setup and Usage Guide

## Overview

pgAdmin is a web-based PostgreSQL administration and development platform. The AI Agent API includes pgAdmin in its Docker Compose infrastructure for easy database management and query execution during development.

## Quick Start

### Access pgAdmin

**URL**: http://localhost:5050

**Login Credentials**:
- **Email**: admin@aiagent.dev
- **Password**: admin

### Database Connection

The PostgreSQL database is **automatically configured** in pgAdmin:

- **Server Name**: AI Agent Local
- **Host**: postgres (Docker internal hostname)
- **Port**: 5432
- **Database**: aiagent_db
- **Username**: aiagent
- **Password**: password (auto-filled via pgpass file)

## Architecture

### Docker Configuration

pgAdmin is configured in both development and production docker-compose files:

#### docker-compose.dev.yml (Development)
```yaml
pgadmin:
  image: dpage/pgadmin4:latest
  container_name: aiagent-pgadmin-dev
  restart: unless-stopped
  environment:
    PGADMIN_DEFAULT_EMAIL: admin@aiagent.dev
    PGADMIN_DEFAULT_PASSWORD: admin
    PGADMIN_CONFIG_SERVER_MODE: 'False'
    PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
  ports:
    - "5050:80"
  volumes:
    - pgadmin_dev_data:/var/lib/pgadmin
    - ./pgadmin-servers.json:/pgadmin4/servers.json:ro
    - ./pgadmin-pgpass:/tmp/pgpassfile:ro
  networks:
    - aiagent-dev-network
  depends_on:
    postgres:
      condition: service_healthy
```

#### docker-compose.yml (Production)
Similar configuration but without `-dev` suffix in names.

### Configuration Files

#### 1. pgadmin-servers.json

This file contains the pre-configured PostgreSQL server connection:

```json
{
  "Servers": {
    "1": {
      "Name": "AI Agent Local",
      "Group": "Development",
      "Host": "postgres",
      "Port": 5432,
      "MaintenanceDB": "aiagent_db",
      "Username": "aiagent",
      "SSLMode": "prefer",
      "PassFile": "/tmp/pgpassfile",
      "Comment": "AI Agent development database"
    }
  }
}
```

**Key Fields**:
- `Name`: Display name for the server in pgAdmin UI
- `Host`: PostgreSQL hostname (uses Docker service name)
- `PassFile`: Path to password file for automatic authentication
- `SSLMode`: SSL connection preference (prefer = try SSL, fall back to non-SSL)

#### 2. pgadmin-pgpass

PostgreSQL password file for automatic authentication:

```
postgres:5432:aiagent_db:aiagent:password
```

**Format**: `host:port:database:username:password`

**Permissions**: Should be readable only by pgAdmin container

### Environment Variables

pgAdmin uses the following environment variables:

- `PGADMIN_DEFAULT_EMAIL`: Initial admin email for login
- `PGADMIN_DEFAULT_PASSWORD`: Initial admin password for login
- `PGADMIN_CONFIG_SERVER_MODE`: Set to `'False'` for single-user mode
- `PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED`: Set to `'False'` to skip master password prompt

## Common Tasks

### Connect to Database

1. Navigate to http://localhost:5050
2. Login with credentials above
3. The "AI Agent Local" server appears in the left sidebar
4. Expand it to see databases, schemas, and tables

### Run SQL Queries

1. Right-click "AI Agent Local" → **Query Tool**
2. Write SQL in the editor
3. Click **Execute** or press F5
4. Results appear in the bottom panel

### View Table Data

1. Expand "AI Agent Local" → Databases → aiagent_db → Schemas → public → Tables
2. Right-click any table → **View/Edit Data** → **All Rows**
3. Table data displays in a grid

### Create Backup

1. Right-click "AI Agent Local" → **Backup**
2. Choose backup options
3. Select location to save backup file
4. Click **Backup**

### Restore Backup

1. Right-click "AI Agent Local" → **Restore**
2. Select backup file
3. Click **Restore**

### View Query Performance

1. Open **Query Tool**
2. Write your query
3. Click **Explain** for query plan
4. Click **Analyze** to run and analyze query

## Development Workflows

### Inspecting Database Schema

1. Access pgAdmin at http://localhost:5050
2. Navigate through the object browser to view tables, columns, indexes, and constraints
3. Use the **Properties** panel to see detailed information

### Data Validation

1. Use Query Tool to write validation queries
2. Check data integrity before deployments
3. Verify migrations completed successfully

### Performance Analysis

1. Use **Query Tool** → **Explain** to analyze query plans
2. Identify slow queries and optimization opportunities
3. Check table statistics and index usage

## Troubleshooting

### pgAdmin Not Accessible

**Symptom**: Cannot access http://localhost:5050

**Solution**:
```bash
# Check container status
docker compose -f docker-compose.dev.yml ps pgadmin

# View logs
docker compose -f docker-compose.dev.yml logs pgadmin

# Restart container
docker compose -f docker-compose.dev.yml restart pgadmin
```

### Database Connection Error

**Symptom**: "Unable to connect to server" in pgAdmin

**Solution**:
1. Verify PostgreSQL container is healthy:
   ```bash
   docker compose -f docker-compose.dev.yml ps postgres
   ```
2. Check container network:
   ```bash
   docker network inspect ai-agent-api_aiagent-dev-network
   ```
3. Verify pgpass file has correct permissions (readable)
4. Check pgadmin-servers.json syntax is valid JSON

### Login Issues

**Symptom**: Cannot login to pgAdmin

**Solution**:
- Clear browser cookies and cache
- Try incognito/private browsing mode
- Reset credentials in docker-compose file and restart container

### Performance Issues

**Symptom**: pgAdmin is slow or unresponsive

**Solution**:
1. Check available disk space: `df -h`
2. Check Docker memory usage: `docker stats`
3. Restart pgAdmin: `docker compose -f docker-compose.dev.yml restart pgadmin`
4. Check pgAdmin logs for errors

## Security Notes

### Development vs Production

**Development (Current Setup)**:
- Server mode disabled (single-user)
- Master password not required
- Credentials in plaintext files (acceptable for dev only)
- No SSL/TLS enabled by default

**Production Considerations**:
- Enable server mode for multi-user access
- Require master password
- Use environment variables for sensitive credentials
- Enable SSL/TLS
- Implement authentication with external providers (LDAP, OAuth)
- Restrict network access with firewall rules

### Password Management

Credentials are stored in:
- `pgadmin-servers.json`: Server configuration (connection details)
- `pgadmin-pgpass`: PostgreSQL password file

**Security Best Practices**:
1. Do not commit pgadmin-pgpass to version control
2. Use strong passwords in production
3. Rotate credentials regularly
4. Use environment variables instead of files in production
5. Restrict file permissions: `chmod 600 pgadmin-pgpass`

## Related Commands

### Makefile Commands

```bash
# List all database tables
make db-tables

# Show data from a specific table
make db-show TABLE=users

# Count rows in a table
make db-count TABLE=users

# Start infrastructure (includes pgAdmin)
make infra-start

# Stop infrastructure
make infra-stop

# View infrastructure status
make infra-status
```

### Docker Compose Commands

```bash
# Start pgAdmin only
docker compose -f docker-compose.dev.yml up -d pgadmin

# Stop pgAdmin
docker compose -f docker-compose.dev.yml down

# View pgAdmin logs
docker compose -f docker-compose.dev.yml logs -f pgadmin

# Access pgAdmin container shell
docker compose -f docker-compose.dev.yml exec pgadmin bash
```

## References

- [pgAdmin Official Documentation](https://www.pgadmin.org/docs/)
- [pgAdmin Server Configuration](https://www.pgadmin.org/docs/pgadmin4/latest/server_management.html)
- [PostgreSQL Password File Format](https://www.postgresql.org/docs/current/libpq-pgpass.html)
- [Docker pgAdmin Image](https://hub.docker.com/r/dpage/pgadmin4)

## Example Queries

### List All Tables

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Count Records in Each Table

```sql
SELECT schemaname, tablename,
  (SELECT COUNT(*) FROM (SELECT 1 FROM pg_class pc
    JOIN pg_namespace pn ON pn.oid = pc.relnamespace
    WHERE pn.nspname = schemaname AND pc.relname = tablename LIMIT 1) AS t) AS row_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### View Active Connections

```sql
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE state IS NOT NULL
ORDER BY pid;
```

### List Table Sizes

```sql
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Getting Help

For issues or questions about pgAdmin:

1. Check the troubleshooting section above
2. Review pgAdmin logs: `docker compose -f docker-compose.dev.yml logs pgadmin`
3. Consult [pgAdmin Documentation](https://www.pgadmin.org/docs/)
4. Check database health with: `make db-tables`

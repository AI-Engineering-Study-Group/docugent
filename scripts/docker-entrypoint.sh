#!/bin/bash

# Docker entrypoint script for backend service
# This script runs database migrations and initialization before starting the app

set -e

echo "Starting API Conference Backend..."

# Wait for database to be ready (with better cloud database support)
echo "Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    echo "Attempt $attempt/$max_attempts: Testing database connection..."
    
    if poetry run python -c "
import asyncio
import asyncpg
import os
import sys

async def test_connection():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.execute('SELECT 1')
        await conn.close()
        return True
    except Exception as e:
        print(f'Connection failed: {e}')
        return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        echo "Database connection successful!"
        break
    else
        echo "Database not ready, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Failed to connect to database after $max_attempts attempts"
    echo "Please check your DATABASE_URL environment variable"
    exit 1
fi

echo "✅ Database is ready!"

# Run Alembic migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Check if database is initialized (check for roles table)
echo "Checking if database needs initialization..."
ROLES_EXISTS=$(poetry run python -c "
import asyncio
import asyncpg
import os
import sys

async def check_roles_table():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        result = await conn.fetchval(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'roles')\"
        )
        await conn.close()
        return result
    except Exception as e:
        print(f'Error checking roles table: {e}')
        return False

result = asyncio.run(check_roles_table())
print('true' if result else 'false')
")

if [ "$ROLES_EXISTS" = "false" ]; then
    echo "Database not initialized, running initialization script..."
    poetry run python scripts/init_db.py
    echo "✅ Database initialization completed!"
else
    echo "✅ Database already initialized, skipping initialization."
fi

# Start the application
echo "Starting FastAPI application..."
exec poetry run uvicorn main:app --host 0.0.0.0 --port 8000

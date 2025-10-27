#!/bin/bash

# E2E Test Runner with Redis Support
# This script starts Redis, runs E2E tests, and cleans up

set -e

echo "🚀 Starting E2E Tests with Redis..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Redis and Elasticsearch containers
echo "📦 Starting Redis and Elasticsearch containers..."
docker-compose -f docker-compose.test.yml up -d redis elasticsearch

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
timeout=30
counter=0
while ! docker exec $(docker-compose -f docker-compose.test.yml ps -q redis) redis-cli ping > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ Redis failed to start within $timeout seconds"
        docker-compose -f docker-compose.test.yml logs redis
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
done

echo "✅ Redis is ready!"

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to be ready..."
timeout=60
counter=0
while ! curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ Elasticsearch failed to start within $timeout seconds"
        docker-compose -f docker-compose.test.yml logs elasticsearch
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
done

echo "✅ Elasticsearch is ready!"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Run E2E tests
echo "🧪 Running E2E tests..."
pytest e2e_tests/ -v --tb=short

# Capture exit code
TEST_EXIT_CODE=$?

# Clean up
echo "🧹 Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

# Exit with test result
exit $TEST_EXIT_CODE
